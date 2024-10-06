# AI Horde Request/Job Lifecycle

The [AI Horde](definitions.md#ai-horde) system follows a specific lifecycle for processing [requests](definitions.md#request) and [jobs](definitions.md#job). This detailed overview explains the flow from submission to completion, including the role of [kudos](kudos.md) in the process.

## 1. User Request Submission

- A [user](definitions.md#user) submits a request to the AI Horde [API](definitions.md#api).
- The request includes details such as the prompt, desired [model](definitions.md#model), and specific parameters (e.g., image dimensions, number of images, steps, etc.).
- The user's kudos balance affects their priority in the queue. Users with more kudos generally have their requests processed sooner.

## 2. Server Validation and Processing

- The server validates the incoming request.
- The user's kudos balance is checked. 
   - If the request *requires* kudos, the user's current kudos balance is checked that it can cover the generation's cost.
   - If the request does not require kudos (an anonymous user could otherwise request it), the kudos are still subtracted in exchange for priority. If the user does not have enough kudos and the user is a registered user, they are treated as having 25 kudos and cannot go below that amount.
      - See [kudos](kudos.md) for more information.
- If valid, the request is added to the pending requests queue.
- The server breaks down the request into individual "jobs" or "generations".
  - Each logically separate result becomes a job (e.g., each image in a multi-image request).
- If the job falls outside certain thresholds, the requesting user must have a sufficient kudos balance for the job to be allowed.

## 3. Worker Assignment and Job Handling

- [Workers](definitions.md#worker) continuously poll for jobs when their local queue has room.
- Job assignment process:
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

- The worker prepares the final Job Submit payload.
- For multiple generations, a submission for each generation is prepared.
- The worker attempts to upload each result (if applicable, e.g., for images).
- If unrecoverable failures occur before this point:
  - The Job Submit payload notifies that the job faulted.
  - The API is notified to minimize delay before reassigning the job.
- The final Job Submit payload(s) are submitted to the API.
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

