# NarReddit Web App Backend

The backbone behind [NarReddit's Web App](http://narreddit.com), this repository houses the containerized backend architecture that powers our seamless conversion of top-rated Reddit posts into engaging video content. 

## Architecture Overview

- **Containerized Design**: The entire backend architecture is containerized for easier deployment, scalability, and separation of concerns.

- **Flask Container (API)**: The primary entrypoint to the video creation service, `app.py`, acts as an API endpoint, catering to the frontend requests and initiating background tasks.

- **Task Queue with RQ and Redis**: To handle intensive tasks like video rendering, we utilize RQ (Redis Queue) which provides a lightweight, Pythonic interface for background job management. Redis acts as the backbone store for this task management, ensuring speedy task delegation and retrieval.

- **Worker Container**: `worker.py` is our dedicated worker service, responsible for processing tasks dispatched by the Flask container. With a containerized approach, we can easily scale the number of workers based on demand.
