import os
import uuid
import ssl
import base64
import threading
import time
from datetime import datetime, timedelta
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
)
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from models import MediaInfo as MediaInfoModel
from mediainfo_parser import MediaInfoParser
from database import Database

load_dotenv()


class MediaInfoShare:
    def __init__(self):
        self.app = Flask(__name__)
        self.db = Database()
        self.parser = MediaInfoParser()
        self._setup_config()
        self._setup_routes()
        self._setup_context_processors()
        self._setup_cleanup_task()
        self._setup_error_handlers()

    def _setup_config(self):
        try:
            key = os.getenv("ENCRYPTION_KEY")
            if not key:
                key = Fernet.generate_key().decode()
            else:
                key = key.encode()
                key = base64.urlsafe_b64encode(base64.urlsafe_b64decode(key)).decode()
        except Exception:
            key = Fernet.generate_key().decode()

        self.app.config.update(
            FLASK_ENV=os.getenv("FLASK_ENV", "development"),
            DEBUG=os.getenv("FLASK_DEBUG", "1") == "1",
            HOST=os.getenv("FLASK_RUN_HOST", "0.0.0.0"),
            PORT=int(os.getenv("FLASK_RUN_PORT", "5000")),
            SSL_CERT_PATH=os.getenv("SSL_CERT_PATH", "./cert.pem"),
            SSL_KEY_PATH=os.getenv("SSL_KEY_PATH", "./key.pem"),
            USE_SSL=os.getenv("USE_SSL", "false").lower() == "true",
            UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER", "static/media"),
            MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH", "1048576")),
            ALLOWED_EXTENSIONS=os.getenv("ALLOWED_EXTENSIONS", "txt").split(","),
            SECRET_KEY=os.getenv("SECRET_KEY", os.urandom(24).hex()),
            ENCRYPTION_KEY=key,
            DONATION_ADDRESSES={
                "BTC": os.getenv("BTC_ADDRESS", ""),
                "ETH": os.getenv("ETH_ADDRESS", ""),
                "USDC": os.getenv("USDC_ADDRESS", ""),
                "LTC": os.getenv("LTC_ADDRESS", ""),
            },
        )

        self.cipher = Fernet(self.app.config["ENCRYPTION_KEY"].encode())
        os.makedirs(self.app.config["UPLOAD_FOLDER"], exist_ok=True)

    def _setup_routes(self):
        @self.app.route("/", methods=["GET", "POST"])
        def index():
            if request.method == "POST":
                mediainfo_text = request.form.get("mediainfo")
                if not mediainfo_text:
                    flash("Please provide MediaInfo output.")
                    return redirect(url_for("index"))

                filename = f"{uuid.uuid4().hex}_mediainfo.txt"
                file_path = os.path.join(self.app.config["UPLOAD_FOLDER"], filename)

                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(mediainfo_text)

                    parsed_info = self.parser.parse_file(file_path)
                    media = MediaInfoModel(
                        id=str(uuid.uuid4()),
                        filename=filename,
                        original_filename="MediaInfo Output",
                        uploaded_on=datetime.now(),
                        expiration=datetime.now() + timedelta(hours=24),
                        raw_output=mediainfo_text,
                        parsed_info=parsed_info
                    )

                    if not self.db.save_media_info(media):
                        flash("Error saving media information.")
                        return redirect(url_for("index"))

                    return redirect(url_for("preview", media_id=media.id))
                except Exception as e:
                    flash(f"Error processing file: {str(e)}")
                    return redirect(url_for("index"))

            return render_template("index.html")

        @self.app.route("/share/<media_id>", methods=["GET", "POST"])
        def share(media_id):
            media = self.db.get_media_info(media_id)
            if not media:
                flash("Invalid or expired link.")
                return redirect(url_for("index"))

            if media.expiration and datetime.now() > media.expiration:
                flash("This link has expired.")
                return redirect(url_for("index"))

            if media.password:
                if request.method == "POST":
                    if request.form.get("password") != self._decrypt_password(
                        media.password
                    ):
                        flash("Incorrect password. Please try again.")
                        return render_template(
                            "share.html", media_info=None, error=True, media_id=media_id
                        )
                else:
                    return render_template(
                        "share.html", media_info=None, error=False, media_id=media_id
                    )

            return render_template("share.html", media_info=media, media_id=media_id)

        @self.app.route("/preview/<media_id>", methods=["GET"])
        def preview(media_id):
            media = self.db.get_media_info(media_id)
            if not media:
                flash("Invalid or expired link.")
                return redirect(url_for("index"))

            if media.expiration and datetime.now() > media.expiration:
                flash("This link has expired.")
                return redirect(url_for("index"))

            return render_template("preview.html", media_info=media, media_id=media_id)

        @self.app.route("/download/<media_id>", methods=["GET", "POST"])
        def download(media_id):
            media = self.db.get_media_info(media_id)
            if not media:
                flash("Invalid or expired link.")
                return redirect(url_for("index"))

            if media.expiration and datetime.now() > media.expiration:
                flash("This link has expired.")
                return redirect(url_for("index"))

            if media.password:
                if request.method == "POST":
                    if request.form.get("password") != self._decrypt_password(
                        media.password
                    ):
                        flash("Incorrect password. Please try again.")
                        return render_template(
                            "share.html", media_info=None, error=True
                        )
                else:
                    return render_template("share.html", media_info=None, error=False)

            file_path = os.path.join(self.app.config["UPLOAD_FOLDER"], media.filename)
            if not os.path.exists(file_path):
                flash("File not found.")
                return redirect(url_for("index"))

            return send_from_directory(
                self.app.config["UPLOAD_FOLDER"], media.filename, as_attachment=True
            )

        @self.app.route("/donate")
        def donate():
            return render_template("donate.html")

    def _setup_context_processors(self):
        @self.app.context_processor
        def inject_datetime():
            return {"datetime": datetime}

        @self.app.context_processor
        def inject_enumerate():
            return {"enumerate": enumerate}

        @self.app.context_processor
        def inject_donation_addresses():
            return {"donation_addresses": self.app.config["DONATION_ADDRESSES"]}

    def _encrypt_password(self, password: str) -> str:
        return self.cipher.encrypt(password.encode()).decode() if password else None

    def _decrypt_password(self, encrypted_password: str) -> str:
        return (
            self.cipher.decrypt(encrypted_password.encode()).decode()
            if encrypted_password
            else None
        )

    def _setup_cleanup_task(self):
        def cleanup_task():
            while True:
                try:
                    expired_count = self.db.delete_expired_media()
                    if expired_count > 0:
                        print(f"Cleaned up {expired_count} expired media entries")
                except Exception as e:
                    print(f"Error during cleanup: {str(e)}")
                time.sleep(3600)

        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()

    def _setup_error_handlers(self):
        @self.app.errorhandler(404)
        def not_found_error(error):
            return render_template('error.html',
                error_code=404,
                error_title="Page Not Found",
                error_description="The page you're looking for doesn't exist or has been moved."
            ), 404

        @self.app.errorhandler(403)
        def forbidden_error(error):
            return render_template('error.html',
                error_code=403,
                error_title="Forbidden",
                error_description="You don't have permission to access this resource."
            ), 403

        @self.app.errorhandler(500)
        def internal_error(error):
            return render_template('error.html',
                error_code=500,
                error_title="Internal Server Error",
                error_description="Something went wrong on our end. Please try again later."
            ), 500

        @self.app.errorhandler(Exception)
        def unhandled_exception(error):
            return render_template('error.html',
                error_code=500,
                error_title="Unexpected Error",
                error_description=str(error) if self.app.debug else "An unexpected error occurred."
            ), 500

    def run(self):
        expired_count = self.db.delete_expired_media()
        if expired_count > 0:
            print(f"Cleaned up {expired_count} expired media entries")

        ssl_context = None
        if self.app.config["USE_SSL"]:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            ssl_context.load_cert_chain(
                self.app.config["SSL_CERT_PATH"], self.app.config["SSL_KEY_PATH"]
            )

        self.app.run(
            host=self.app.config["HOST"],
            port=self.app.config["PORT"],
            debug=self.app.config["DEBUG"],
            ssl_context=ssl_context,
        )


if __name__ == "__main__":
    app = MediaInfoShare()
    app.run()
