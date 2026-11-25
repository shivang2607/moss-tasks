# Shivang's original notes for the Moss work sample

The text below is preserved as written by Shivang. It is his first-hand feedback and interpretation, not an independently verified benchmark result.

> Portal:
> liked : the idea of providing the code snippet of what the user is running in the portal is really a good idea, The UI and screen recording which is shown for the tasks is pretty cool
> disliked: page was loading a lot of time to load and to route to other URLs, while I submitted a document for index and navigated to differnt page and came back my submission was not there and when i tried to submit it showd a submission is in progress. Also I was not able to find my total available credits.
> What I would change: Firsly, improve performance of the pages, then I would focus on improving the state mangement and UX
>
> Inference API:
> liked: the 10-16ms retrieval really is very fast, I tested with the competitor graphify which also can create a KB of pdf documents and moss really performed better in that context.
> disliked: I have my own doubts about retrieval, due to time constraints I was not able to test properly but I think that for general queries it can perform good maybe because the model also has that knowledge, but wether it can retrieve the data effieciently in case a user asked some specific questions on or something on which it has not been trained I think there is room of improvement in the retrieval.
> What I would change : currently indexing only supports md, text or pdf documents, but most developers want the code retrieval and want the code to be indexed, even though a md file cna exist for that It won't perform as good. So an option for indexing code itself should be there (by the way in devlens I am working on this and that is why i am specially interested in the code indexing and the retrieval algorithm)
>
> Tasks API:
> liked: The WEB UI recording showing how it searched is really intresting and cool. Most intresting part is that I saw it solving a captcha which was meant to be solved by human XD.
> disliked: accuracy was not on par with chatGPT even with deepseek model. I asked it to suggest me the cheapest VPS for 16GB RAM, but I think it just returned the results which were first listed. Chat GPT did better work.
> What I would change: I do not know the underlying architecture, but when we talk something about "Tasks" research is needed and a different approach should be taken for that purpose. I do not have expertise in this domain but I will see where I can improve.
