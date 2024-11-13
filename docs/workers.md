# AI Horde Request/Job Lifecycle

The [AI Horde](definitions.md#ai-horde) system efficiently processes user requests through a structured lifecycle, ensuring fair resource allocation and timely completion of tasks. This document provides a comprehensive overview of each stage in the lifecycle, from initial request submission to final result retrieval, highlighting the role of [kudos](kudos.md) in prioritizing and rewarding contributions.

See also the [job lifecycle diagram](job_lifecycle.md) and [worker loop diagram](worker_loop.md).

## 1. User Request Submission

- A [user](definitions.md#user) submits a request to the AI Horde [API](definitions.md#api).
- The request includes details such as the prompt, desired [model](definitions.md#model), and specific parameters (e.g., image dimensions, number of images, steps, etc.).
- The user's kudos balance affects their priority in the queue. Users with more kudos generally have their requests processed sooner.

## 2. Server Validation and Processing

| Step | Description | Valid Result | Invalid Result |
|------|-------------|--------------|----------------|
| **1. Request Validation** | The server validates the incoming request against the published parameter constraints. | Continues to the next step. | Request is rejected, notifying the user of the specific field(s) causing the error. |
| **2. Threshold Check** | If the job falls outside certain thresholds (such as resolution, for image requests), the requesting user must have a sufficient kudos balance for the job to be allowed. If `allow_downgrade` is enabled, the job parameters may instead be adjusted in order to continue. | Continues to the next step. `allow_downgrade` may adjust job parameters. | Request is rejected. |
| - **Job Does Not Require Kudos** | If the request does not require kudos (e.g., an anonymous user could make this request), kudos are still subtracted in exchange for priority, if possible. | Kudos are subtracted if available. | Treated as having 25 kudos if the user is registered. |
| *or* | | | |
| - **Job Requires Kudos** | If the request requires kudos, the user's current kudos balance is checked to ensure it can cover the generation's cost. | Kudos must be subtracted from user's account. | Request is rejected. |
| **3. Job Breakdown** | The server breaks down the request into individual "jobs" or "generations". Each logically separate result becomes a job (e.g., each image in a multi-image request). | Continues to the next phase. | Request is rejected. |
| **4. Add to Queue** | If valid, the job(s) are added to the pending requests queue. | Available for worker assignment | |

## 3. Worker Assignment and Job Handling

- [Workers](definitions.md#worker) continuously poll for jobs when their local queue has room. However, they are not required to have jobs queued or their queue full. Workers never listen on a port for jobs - they always reach out to the API for work.
- Certain worker types analyze the latest popped job and pause popping new jobs until the already queued jobs make some progress.
  - Consider the following scenario:
    - A worker pops a job ('Job L') expected to take 3 minutes.
    - The worker immediately pops another job ('Job S') expected to take 20 seconds.
    - 'Job L' will need to finish before 'Job S' can begin.
    - The end user, expecting a quick response, would instead see it take over 3 minutes to get a response. If the worker had popped more conservatively, another worker could have handled 'Job S' more quickly, providing a faster response to the user.
    - By pausing job pops until 'Job L' has made significant progress, the worker can help reduce wait times for end users.
  - However, it is important to note that workers typically require between 3 and 20 seconds per job to preload assets into memory.
  - Therefore, it is prudent for workers to have some overlap between jobs, aiming to pop a new job with around 30 seconds left on long-running jobs, and aiming to pop another instantly when the already queued jobs are expected to be brief.

### Job assignment process

1. If a job is available and matches the worker's capabilities, based on [kudos priority](kudos.md#priority-system):
    - The worker receives a job [payload](definitions.md#payload) with a unique generation UUID.
    - For workers configured to handle multiple generations, multiple UUIDs may be provided.
2. The job is queued for execution if the worker is currently busy.
3. The required model begins loading into system memory immediately or as soon as resources are available.
4. Once the previous generation (if any) is complete, work begins on the new generation.

## 4. Job Execution and Processing

- The worker processes the job according to the specified parameters.
- [Post-processing](definitions.md#post-processing) is performed if applicable (e.g., upscaling for images).
- For [image generation](definitions.md#text2img), safety checks are conducted:
  - NSFW content is filtered if requested by the user.
  - Checks for illegal content are always performed.

## 5. Result Submission

1. The worker prepares the final Job Submit payload.
    - For multiple generations, a submission for each generation is prepared.
2. The worker attempts to upload each result (if applicable, e.g., for images).
    - If unrecoverable failures occur before this point:
        - The Job Submit payload notifies that the job faulted.
        - The API is notified to minimize delay before reassigning the job.
3. The final Job Submit payload(s) are submitted to the API.
    - Repeated submission failures may lead to the job being abandoned client-side.
    - The API eventually times out abandoned jobs and reassigns them if possible.

## 6. Request Completion and Result Retrieval

- Once all jobs for a request are completed, the user can retrieve the results.
- The retrieval process differs based on the request type:
  - [Text Requests](definitions.md#text2text):
    - Users poll the relevant 'status' endpoint to check progress and receive the final generation data.
  - [Image Requests](definitions.md#image-generation):
    - Users first poll the relevant 'check' endpoint to monitor progress.
      - This endpoint has less restrictive rate limits but doesn't return the final image data.
      - It indicates completion with a `done: true` field.
    - Once complete or partially complete, users can use the 'status' endpoint to retrieve the generated images.

## 7. Kudos Distribution

- Upon successful completion of a job, the worker is awarded [kudos](kudos.md).
- The amount of kudos awarded is based on the complexity and resource requirements of the job.
- Workers also receive a nominal amount of kudos for being online and available, awarded in 10-minute increments.
- These earned kudos can be used by the worker's owner for their own requests or left unspent, effectively contributing to the broader AI Horde community.
- See the full explanation of kudos on the [dedicated page](kudos.md).

## Worker Types and Technologies

The AI Horde supports various types of workers:

1. [Image Generation Workers](definitions.md#dreamer)

   - Technologies: [Stable Diffusion](definitions.md#stable-diffusion) (SD1.5, SD2.1, SDXL, "Stable Cascade"), Flux Schnell
   - The official worker is powered by [ComfyUI](definitions.md#comfyui), potentially allowing for any ComfyUI-supported model (license permitting).
   - Generated images undergo checks for potentially illegal content:
     - Images failing checks are deleted and replaced with a warning image.
     - Multiple control layers include prompt analysis, machine vision, and human review.

2. [Image Alchemy Workers](definitions.md#alchemist)

   - Perform tasks like AI-model based upscaling, face-fixing (e.g., codeformers), and other image processing.
   - Some alchemy operations can be part of the initial image generation process, improving response times.

3. [Text Generation Workers](definitions.md#scribe)
   - Utilize a wide variety of [Large Language Models (LLMs)](definitions.md#llm).
   - The full list of supported models is available in the official [AI Horde text model reference](definitions.md#text-model-reference).

Each worker type specializes in specific tasks within the AI Horde ecosystem, contributing to the overall functionality and versatility of the service. Workers earn [kudos](kudos.md) for their contributions, which helps maintain a fair and efficient system for resource allocation.
