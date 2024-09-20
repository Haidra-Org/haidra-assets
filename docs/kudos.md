# Kudos

## Overview
The [AI Horde](definitions.md#ai-horde) service relies on volunteer compute resources (primarily GPUs) to provide [users](definitions.md#user) with generative AI results (as well as other forms of processing). When a user submits a [request](definitions.md#request) to the server, it is dispatched to the first available [worker](definitions.md#worker) for processing. A value is assigned to each [job](definitions.md#job), called 'kudos'. If the job falls outside of certain thresholds, the requesting user must have this amount of kudos in their account for the job to be allowed.

Regardless of whether the requesting user has the kudos, if the request is allowed and is successfully completed by a worker, that worker is awarded the same number of kudos. Finally, workers receive a nominal amount of kudos merely for being online and available, in 10-minute increments. This ensures a steady pool of workers and rewards availability, even when there is not a task currently available to process.

This means that **kudos are the fundamental unit of exchange of resources on the AI Horde**. If you offer your services as a worker on the AI Horde, you will always be able to "cash out" an equal amount of effort back out of the AI Horde.

## Kudos Key Takeaways
- **Kudos never expire.**
- **It is against the [Terms of Service](https://aihorde.net/terms) to sell or buy kudos.**
  - We *do* offer kudos as a thank-you if you [donate](https://www.patreon.com/db0), however, the kudos you receive are offset by kudos earned by workers run by the core developers.
  - Kudos *can* be freely exchanged between users for any reason other than for currency (legal tender, crypto, or any other similar unit of exchange).
  - For example, users may gift kudos to each other as a gesture of gratitude or to support new members of the community.
- **Kudos are designed to facilitate fair exchange of compute resources and prevent commodification.**
  - This ensures that access to resources remains equitable and prevents external financial pressures from distorting the kudos system.
- **The total number of kudos in your account determines your starting place in line when queuing a job.**
  - The more kudos you have in your account, the higher priority your job will have in the queue. Anonymous users start with 0 kudos, while registered users have at least 25, giving them an advantage when queuing jobs.
  - If two users have the same kudos and they were to submit a job at the same time, they can expect that both jobs would return in about the same amount of time.

![Kudos Flow Diagram](kudos_flow.png)

## Priority System
The kudos-based priority system ensures fair access to the AI Horde's resources. When a user submits a request, their position in the job queue is determined by the number of kudos in their account. Users with more kudos will have their jobs processed sooner, while those with fewer kudos may experience longer waiting times.

However, the AI Horde has measures in place to prevent kudos hoarding and ensure that users with large amounts of kudos do not dominate the platform. These measures include:
- Limiting the maximum number of kudos a user can accumulate
- Monitoring and flagging suspicious activity, such as the use of multiple accounts to circumvent kudos limits

By striking a balance between rewarding contributors and ensuring fair access for all users, the kudos-based priority system maintains the integrity and equity of the AI Horde ecosystem.

## Why Earn Kudos?
Here are some practical reasons why participating as a worker in the AI Horde system might be beneficial to you or your service:

- **Reducing GPU/compute downtime**
  - If you offer a service that has infrequent (or at least, not-constant) usage, you can "bank" kudos from the AI Horde by running a worker. If it is configured correctly and with sufficiently popular models, it will have a continuous amount of work generating kudos.
  - By earning kudos during periods of downtime, you can later use them when you need faster or higher-end services from the platform.

- **Converting lower-end GPUs to higher-end results**
  - Lower-end GPUs are still valuable to many users, but the models they can run (like SD1.5 or smaller low-parameter text models) might not meet your needs. By operating a worker and accumulating kudos, you can use the compute time from your lower-end GPU to request results from more powerful GPUs capable of running larger models.

- **Improved instantaneous concurrency**
  - On the AI Horde, each generation request is processed by a separate worker. If you need more results per second than your GPU can provide, running a worker allows you to build up kudos and make multiple requests simultaneously.
  - For instance, if you need to generate a batch of 50 images quickly, your kudos allow you to split the work across multiple workers, drastically reducing the time required for completion.

- **Altruism**
  - Most kudos earned by workers go unspent. Unspent kudos are effectively a donation to users of the service who do not have kudos.
  - By earning and leaving kudos unspent, workers contribute to the broader public, ensuring that users without kudos can still benefit from the platform.
  - Workers may have [ideological reasons](why.md) such as supporting open-source initiatives, promoting decentralized AI development, or ensuring fair access to generative AI tools.

### Use Cases
- **Content Creators**: Artists, writers, and designers can use their kudos to generate high-quality images, text, or other content to enhance their creative projects, even if they don't have access to powerful hardware.
- **Developers**: Developers can accumulate kudos by running workers during off-peak hours, then use those kudos to speed up testing and development of their AI-powered applications.
- **Researchers**: Researchers can leverage the kudos system to access a wide range of models and resources, enabling them to conduct experiments and validate their findings without the need for expensive hardware investments.

## Conclusion
The kudos system is integral to maintaining the AI Horde's collaborative, decentralized infrastructure. It incentivizes workers to contribute their compute power, ensures fair distribution of resources, and preserves the platform's commitment to free access for all users. By aligning contributions with rewards, kudos enable efficient task processing while supporting a thriving, open-source community that values cooperation over commodification. Whether reducing downtime, trading compute power, or simply contributing to a broader cause, kudos offer both practical and ideological value to participants in the AI Horde ecosystem.
