# AI Horde Detailed Glossary

Below is a list of terms that you may encounter when utilizing or developing for the AI-Horde. Note that many of these definitions are not comprehensive and may only explore their impact or meaning specific to the AI-Horde. Also, be aware that documentation has a tendency to become outdated, so the definitions given here may lack context or be out of date due to changes that have happened since the time of writing/updating.

## Core Concepts

### AI Horde

The `AI Horde` refers to the core middleware ([API](#api)) responsible for smart queuing and clustering tasks. The [official AI Horde](https://aihorde.net) is currently the only public instance, but others can create private or public AI Hordes as well. Each AI Horde operates independently, meaning they do not share [workers](#worker), [users](#user), or [kudos](#kudos) with one another.

### API

An [Application Programming Interface](https://en.wikipedia.org/wiki/API) used by programs to communicate requests or receive responses from a service, such as the [AI-Horde](#ai-horde). The AI-Horde API is a [RESTful](https://en.wikipedia.org/wiki/Representational_state_transfer) interface and is available with human-readable documentation at <https://aihorde.net/api>.

See also [horde-sdk](#horde-sdk) for the official Python SDK for interacting with the AI-Horde API.

### Kudos

> See also the [Kudos detailed explanation](kudos.md).

`Kudos` is the priority system that determines which [user](#user)'s request is processed first. [Workers](#worker) earn kudos when they complete a [job](#job), and users spend kudos to make requests. Kudos can be traded but not sold. Users cannot go below a certain minimum, and they can still submit requests even when they have reached their minimum balance.

### Request

The [payload](#payload) sent by the [user](#user) via their chosen [integration](#integration). A request can be for one or more [jobs](#job). Each request receives a unique ID (UUID) for the user who requested it to track its status.

### Job

Each [request](#request) is split into multiple `jobs` so that it can be better parallelized to different [workers](#worker). Each job has a unique ID (UUID) which is not the same as the request UUID. Each job is assigned only to the worker which picked it up and allows the user to track which worker fulfilled it. A worker cannot see any information about the [user](#user) who requested a specific job.

### Payload

The `Payload` refers to data sent to or received from the [API](#api).

For example, a payload for a [text2img](#text2img) [request](#request) would include the [user](#user)'s [API key](#api-key), the prompt, the number of images, the resolution, and the required [model](#model). In contrast, a payload received by a [user](#user) would contain images or the resulting text (if the request was a [text2text request](#text2text)).

## Users and Security

### User

An account existing in an AI Horde and allowed to perform operations in the API. There are three types of users: [oauth2](#oauth2) user, [pseudonymous](#pseudonymous) user, and [anonymous](#anonymous) user. A user only has one [API key](#api-key) at a time which uniquely identifies it.

### API Key

A random assortment of characters identifying a [user](#user) of an [AI Horde](#ai-horde) and allowing use of all operations of the [API](#api). It should be **treated like a password and not shared with anyone**. To share keys, see [Shared Key](#shared-key).

> **Note**: Regenerating an API key for your account with [OAuth](#oauth2) only changes the API key. It does not reset your account. All kudos, worker names, worker stats, and any other account flags are maintained when you regenerate a key. This feature is only meant to be used if your key becomes compromised or you lose your key.

### Shared Key

A UUID identifying a user of an [AI Horde](#ai-horde) which can only be used for generating images or text. It cannot be used for any other purpose and is meant to be shared.

### oauth2

A protocol allowing an [AI Horde](#ai-horde) to identify a [user](#user) using another identity provider. Used because it offloads user management elsewhere. An account registered after logging in with one of the oauth2 services supported by the AI Horde has the highest priority when generating by default. The use of oauth2 for authentication allows the user to change their username or reset their API key.

### Pseudonymous

> **Important**: Pseudonymous accounts cannot be recovered if the user misplaces their [API key](#api-key). If you lose your API key with a pseudonymous account **it will be lost forever**.
>
An account registered without logging in with the [oauth2](#oauth2) services.

### Anonymous

Any user using the `0000000000` [API key](#api-key) is identified as anonymous. They can use the generation capabilities of the AI horde, but they have the lowest priority.

### Terms of Service

All users of the horde, whether through proxied requests or directly, must agree to the official [Terms of Service](https://aihorde.net/terms). Additionally, users of the horde service agree to follow any terms and restrictions for the model they are using for that request.

### Roles

A classification given to a [user](#user) which specifies extra capabilities for their account. This includes certain whitelists (such as the `vpn` role, allowing VPN usage), the `educator` role (given to accounts of educators or educational institutions), and the `customizer` role (which allows offering custom image models).

### Educator (role)

Given to [accounts](#user) which are operated by educators or educational institutions. Accounts with this role are eligible to be highlighted as accounts for users to donate to in order to promote education. Requests made from an educator role account always have the NSFW filter enabled.

### Customizer (role)

Given to trusted and verified [accounts](#user) who wish to offer custom image models not found in the [image model reference](#image-model-reference). Note that this does not grant permission to offer models whose licenses are incompatible with the AI-Horde's Software-as-a-Service model. Additionally, all usual expectations for worker behavior still remain; this only lifts the requirement that the model being offered appear on the image model reference.

### Flag

A classification for a worker or user which specifies extra restrictions.

### Trusted

A [user](#user) who has run a [worker](#worker) for at least one week and generated a significant amount of [kudos](#kudos) through inference. Trusted users get the ability to run a worker behind a VPN, and they cannot get [suspicion](#suspicious) anymore. They also get a special role in the official Discord server.

### Suspicious

Any time a user does something problematic, such as their worker generating images way too fast or picking up many [jobs](#job) and not generating them, they get a suspicion point. Enough of these and a user is marked as suspicious. Suspicious users cannot transfer or be given kudos, and if their worker keeps misbehaving, they might be [paused](#paused). Suspicion can be cleared by [moderators](#moderator) upon request if there's a valid reason.

### Admin

A [user](#user) who has the ability to set new [moderators](#moderator) or modify user kudos.

### Moderator

A [user](#user) who has the ability to set [flags](#flag) or [roles](#roles). They cannot modify kudos or assign moderator roles. They are responsible for ensuring any [malicious actors](#malicious-actor) are quickly dealt with to avoid disrupting the [AI Horde](#ai-horde) operations. Moderators also get a monthly [kudos](#kudos) stipend.

### Malicious Actor

Someone who is attempting to disrupt an AI Horde in some manner or is attempting to violate the [Terms of Service](#terms-of-service).

### Countermeasures

Operations in an [AI Horde](#ai-horde) which attempt to prevent [malicious actors](#malicious-actor) from disrupting operations automatically. For example, a worker which is never returning picked up [jobs](#job) will be automatically set to [maintenance](#maintenance) and eventually [paused](#paused) as a countermeasure. Additionally, certain checks are made to prompts and outputs to ensure compliance with the law.

### Raid

A situation where an [AI Horde](#ai-horde) is being attacked by [malicious actors](#malicious-actor) in some manner. For example, workers picking up jobs and not returning them, or picking up jobs and returning hate speech, etc.

## Infrastructure

### Infrastructure

The infrastructure consists of the servers and software stack that power the AI Horde. The system relies on the following components: Linux, Python 3, HAProxy, PostgreSQL, Redis, and Cloudflare R2.

### R2

Cloudflare R2 is an object storage service used by the AI Horde to store and distribute images. When R2 is enabled in the API, the AI Horde returns a download link to the stored image in R2.

### Horde Tax

An extra amount of kudos burnt whenever a request is put in the horde. They are not given to the worker fulfilling the [job](#job). It represents the [infrastructure](#infrastructure) costs of running the AI Horde. This amount is usually a tiny amount per [request](#request). However, certain parameters, such as the worker `whitelist` or `blacklist` features, also incur an additional kudos tax. Check the [API docs](#api-docs) for more information.

## Integrations

### Integration

Any software that uses the [AI Horde](#ai-horde) [API](#api) to provide functionality is considered an `Integration`.

### Frontend

The `Frontend` is the interface that a [user](#user) directly interacts with to access the [AI Horde](#ai-horde). It translates user inputs into an [API](#api) [payload](#payload). A frontend can be written in any programming language and may run locally, in a browser, or as part of another service, such as a [Bot](#bot). Also known as [Client](#frontend) or [UI](#frontend).

### Bot

A `Bot` is an [AI Horde](#ai-horde) [integration](#integration) hosted on a third-party server, facilitating interactions between another service and the AI Horde. For example, a Discord bot connects Discord with the AI Horde, while a Reddit bot connects Reddit with it.

### Proxy

A `Proxy` is a service that sits between the [Frontend](#frontend) and an [AI Horde](#ai-horde). This means that AI Horde request logic is handled by the proxy servers instead of the [user](#user)'s computer. For example, in a Discord [Bot](#bot), Discord itself (and the `/slash` command therein) is the [Frontend](#frontend) and the bot servers are the proxy. Proxies can read your request details and even store your [API key](#api-key) for re-use later. As such, it's important not to use proxy services you do not trust!

### API Docs

The human-readable [official AI-Horde API Docs](https://stablehorde.net/api/) are designed to give a comprehensive list of the operations available in the AI-Horde as well as all of the headers, paths, and object information requested in order to make such a request.

There is also a [machine-readable swagger.json](https://stablehorde.net/api/swagger.json) available for use with local validation or for automatic API client generation.

### Horde SDK

A Python library for interacting with the AI Horde API. Its goal is to minimize the time required to develop integrations written in Python. It supports Image Generation, Image Captioning, and Image Rating.

### Plugin

A piece of code that is called from within another application to extend its functionalities so that it can talk to the [AI Horde](#ai-horde). For example, the Krita plugin allows Krita to perform [inpainting](#inpainting) on images being worked on.

## Worker/Backend

### Worker

A `Worker` processes jobs received from the AI Horde, such as generating content or performing post-processing. For instance, the [KoboldAI Client](#koboldai-client) is the official worker for a [Scribe](#scribe), while [hordelib](#hordelib) serves as the official worker backend in the official [Dreamer](#dreamer), [horde-worker-reGen](#horde-worker-regen).

### Bridge

A `Bridge` is a software component that handles the communication between the inference [worker](#worker) and the [AI Horde](#ai-horde) via the [API](#api). It also manages local task queuing. Some implementations combine both worker and bridge functionalities in one application.

### Dreamer

An [AI Horde](#ai-horde) [Bridge](#bridge) providing [text2img](#text2img), [img2img](#img2img), and [inpainting](#inpainting) capabilities. Dreamers generate [kudos](#kudos) per image generation with the baseline being 10 kudos for an image of 512x512 pixels at 50 steps. Dreamers also receive uptime kudos every 10 minutes, with the number increasing with the number of [models](#model) they serve at the same time.

### Scribe

An [AI Horde](#ai-horde) [Bridge](#bridge) providing [LLM](#llm) Generation capabilities. Scribes generate [kudos](#kudos) per text generation with the baseline being 10 kudos for 80 [tokens](#token) in a 2.7b model. The kudos generated scale with the number of parameters in the model size. Scribes also receive uptime kudos every 10 minutes, with the number increasing with the parameters in their model.

### Alchemist

An [AI Horde](#ai-horde) [Bridge](#bridge) providing Image [Interrogation](#interrogation) and Image post-processing capabilities. Alchemists generate [kudos](#kudos) per image alchemy with the baseline being 1-3 kudos based on the task difficulty. Alchemists also receive 40 uptime kudos every 10 minutes.

### KoboldAI Client

An open source software capable of providing local [LLM](#llm) Inference. It provides its own REST API, which allows it to be used by the AI Horde as a [worker](#worker). Newer versions come with a built-in [scribe](#scribe).

### ComfyUI

A [FOSS](#foss) local [UI](#frontend) for Stable Diffusion inference written in Python. It is used by [hordelib](#hordelib) to turn it into a Python library. [Repository](https://github.com/comfyanonymous/ComfyUI)

### hordelib

The wrapper around [ComfyUI](#comfyui), turning it into a library which can then be embedded into the official AI Horde [dreamer](#dreamer). Hordelib is provided as [a pypi library](https://pypi.org/project/hordelib/) that can be imported into any other [FOSS](#foss) Python project requiring Stable Diffusion capabilities.

### horde-worker-reGen

The second major iteration of the official image generation client, found at <https://github.com/Haidra-Org/horde-worker-reGen>. This software is a worker and bridge combined, using [hordelib](#hordelib) (and therefore [ComfyUI](#comfyui)) to perform generations.

## Models and Generation

### Model

A trained Machine Learning file which contains the information needed by a [worker](#worker) on how to generate the image or text required. These are generally very large files, from two gigabytes to as much as hundreds.

### Model Reference

In order to maintain payload reproducibility, we maintain lists of known models along with a file integrity hash. This list specifies which models are allowed on the horde and which exact file the worker should use. This includes the [image model reference](#image-model-reference) and the [text model reference](#text-model-reference). The core developers maintain a [Python library](https://github.com/Haidra-Org/horde-model-reference) which handles many aspects of dealing with these files.

### Image Model Reference

Found at <https://github.com/Haidra-Org/AI-Horde-image-model-reference>, it serves as the de-facto list of allowed image generation models. Worker operators who wish to offer models (or versions of the models) that do not appear on this list exactly must have the [customizer role](#customizer-role).

Apologies for the incomplete response. Here's the continuation from the `Text Model Reference` definition:

### Text Model Reference

Found at <https://github.com/Haidra-Org/AI-Horde-text-model-reference>, it serves as the list of previously approved models which are known to the AI-Horde. Workers who offer models whose names appear exactly on this list receive substantially more kudos per request than workers who offer unknown models. It is therefore **strongly recommended** that if you are offering a model, you ensure that if it appears in the model reference, you use the **exact** name that the model reference uses.

### Stable Diffusion

The most popular open source Generative AI [model](#model) for text-to-image operations. [Wikipedia](https://en.wikipedia.org/wiki/Stable_Diffusion)

### LLM

Stands for [Large Language Model](https://en.wikipedia.org/wiki/Large_language_model).

### text2text

Generating text using [LLM](#llm) [models](#model).

### txt2txt

An alternative abbreviation for [text2text](#text2text).

### text2img

See [Wikipedia](https://en.wikipedia.org/wiki/Text-to-image_model). The [AI Horde](#ai-horde) uses [Stable Diffusion](#stable-diffusion).

### txt2img

An alternative abbreviation for [text2img](#text2img).

### img2img

Using an image as the noise source for a Stable Diffusion generation. An img2img can optionally be provided with a [mask](#mask) which points to only a small area of it. It is a less precise version of [inpainting](#inpainting), but its advantage is that it can be run on any model.

### Inpainting

A specialized AI model for changing only parts of an image while keeping the rest intact. Better trained to take context into account compared to [img2img](#img2img) + [mask](#mask).

### Mask

An image matching the resolution of a source image sent to [img2img](#img2img) or [inpainting](#inpainting), but in black and white. Black areas represent the areas to leave intact, while white represents the areas to run inference against.

### img2text

Processing an Image via ML [Models](#model) and figuring out information about it, such as a potential caption or whether it's NSFW. Also known as [Interrogation](#interrogation).

### Image Generation

Any of [text2img](#text2img), [text2img](#text2img) or [inpainting](#inpainting).

### CLIP

CLIP models are used in the [tokenization](#tokenization) of prompts for many image models. CLIP [interrogation](#interrogation) is a technique, using the same models, which can detect whether or not an image contains a particular set of keywords. The AI-Horde uses CLIP interrogation to detect harmful, illegal, or NSFW content.

### BLIP

BLIP models have a similar purpose as [CLIP](#clip) [interrogation](#interrogation), but instead of detecting a list of keywords (as in CLIP), BLIP creates a human language description of the image, called a `caption`.

### Post-Processing

Processing an image and altering it in some way. For example, upscaling it, fixing a badly drawn face, or removing its background. Not to be confused with [img2img](#img2img) or [inpainting](#inpainting).

### Interrogation

The process of extracting information from an image using machine learning [models](#model). This can include generating a caption describing the image's content, identifying objects or people in the image, or determining if the image contains NSFW content. See also [img2text](#img2text), [CLIP](#clip), and [BLIP](#blip).

### NSFW Filter

The NSFW filter is an opt-in feature of image generation which prevents potentially sexually explicit or suggestive content from being returned. At present, this is accomplished using a CLIP model.

### Tokenization

The process of breaking down text into smaller units called [tokens](#token). In the context of [LLMs](#llm), tokenization is a crucial step in preparing the input text for the model. The choice of tokenization method can impact the model's performance and the number of tokens consumed per request.

### Token

A single unit of text after [tokenization](#tokenization). Tokens can be words, subwords, or even individual characters, depending on the tokenization method used. [LLMs](#llm) process text as a sequence of tokens, and the number of tokens in a request is a key factor in determining the computational cost and [kudos](#kudos) consumed.

With these additions, the glossary now covers all the mentioned terms and provides a more comprehensive reference for users and developers working with the AI Horde.

## Flags and Countermeasures

### Maintenance

A [worker](#worker) [flag](#flag) which specifies the worker should not receive any jobs from the horde, even though it keeps polling for [jobs](#job). Maintenance can be set and unset by the worker's owner or by a [moderator](#moderator). Optionally, maintenance can receive a custom message. A worker in maintenance will still pick up jobs from its owner, but they will have to pay the [horde tax](#horde-tax), making using a worker in maintenance a net negative. Maintenance due to being [flagged](#flagged) cannot be unset by the owner.

### Paused

A [worker](#worker) [flag](#flag) which specifies the worker from a [malicious actor](#malicious-actor). A paused worker will still think they're receiving jobs, but they are fake. This is a [countermeasure](#countermeasures) against [raids](#raid).

### Flagged

A user set as flagged will be treated always as [suspicious](#suspicious) and all their workers will be set to [maintenance](#maintenance) which cannot be cleared by their owner. This is a [countermeasure](#countermeasures) against [malicious actors](#malicious-actor).

## Other Concepts

### FOSS

Stands for [Free and Open Source Software](https://en.wikipedia.org/wiki/Free_and_open-source_software).
