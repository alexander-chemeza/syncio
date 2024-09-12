import time
from watchdog.observers  import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from dotenv import load_dotenv
import os
import requests

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TOKEN = os.getenv('TOKEN')
UPLOAD_LINK_URL = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

class Handler(FileSystemEventHandler):
    last_event = None

    def dispatch(self, event: FileSystemEvent) -> None:
        current_event = (event.src_path, event.event_type)
        current_time = time.time()
        if self.last_event and current_event == self.last_event[0] and (current_time - self.last_event[1]) < 1:
            return
        self.last_event = (current_event, current_time)
        super().dispatch(event)

    @staticmethod
    def on_modified(event):
        if not event.is_directory:
            print(f"File {event.src_path} has been modified")

    @staticmethod
    def on_created(event):
        if not event.is_directory:
            print(f"File {event.src_path} has been created")
            upload_file_path = f"/syncio/{event.src_path.split("/")[-1]}"
            local_file_path = event.src_path
            print(f"{upload_file_path}\n{local_file_path}")
            headers = {
                "Authorization": f"OAuth {TOKEN}",
            }
            params = {
                "path": upload_file_path,
                "overwrite": "true"
            }
            response = requests.get(UPLOAD_LINK_URL, headers=headers, params=params)

            if response.status_code == 200:
                upload_link = response.json().get("href")
                with open(local_file_path, 'rb') as file_data:
                    upload_response = requests.put(upload_link, files={'file': file_data})
                    if upload_response.status_code == 201:
                        print('uploaded')
                    else:
                        print(f'error {upload_response.status_code}')
            else:
                print(f'error getting upload link {response.status_code}')

    @staticmethod
    def on_deleted(event):
        if not event.is_directory:
            print(f"File {event.src_path} has been deleted")

class Watcher:
    DIRECTORY_TO_WATCH = os.getenv('DIRECTORY_TO_WATCH')

    def __init__(self) -> None:
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()


if __name__ == "__main__":
    w = Watcher()
    w.run()