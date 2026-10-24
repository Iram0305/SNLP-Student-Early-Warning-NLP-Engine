# Responsible AI Statement
Student Early-Warning NLP Engine — Group 6

## Human Oversight

This system is advisory only. It does not make decisions about students.
It assigns a category and urgency level so that staff can prioritise which
messages to read first. No message is discarded, no student is penalised,
and no action is taken automatically. An academic advisor or support staff
member makes every decision.

Confidence scores support this: predictions below 0.5 confidence are
flagged as low-trust and should be read manually. On our test set, average
confidence was 0.894 when the model was correct and 0.525 when it was
wrong, so the score carries real information.

## Privacy

The dataset is entirely synthetic. All 228 examples were written by the
group as templates; no real student message was collected, stored or
processed at any stage. No personally identifiable information exists
anywhere in this repository.

No data is sent to any external service. The sentence-transformer model is
downloaded once and runs locally. There are no API calls at inference time,
so message content never leaves the machine.

If real institutional data were used in future, it would require
anonymisation and explicit authorisation, and the privacy section of the
dataset documentation would need to be rewritten accordingly.

## Bias

Our message templates were written by five students. Students from
different linguistic, cultural or socioeconomic backgrounds may express
distress in ways our templates do not represent. A student writing in a
second language, or one who understates difficulty, may be assigned a lower
urgency than warranted.

This is a genuine fairness concern for a welfare system, because the cost of
under-detection falls on the students least able to advocate for themselves.
We have not measured this effect, as our synthetic data cannot reveal it.
Evaluating against real, demographically varied messages is the necessary
next step.

## Explainability

The system reports a category, an urgency level and confidence scores, but
cannot currently indicate which words in a message caused the
classification. For a tool touching student welfare this is a limitation:
staff cannot audit an individual decision.

Our error analysis provides partial insight. Two of six urgency errors
share the phrase "I don't understand anything that has been taught", which
lacks the explicit distress wording present in our High-urgency training
examples. This indicates the model keys on specific emotional vocabulary
rather than reasoning about severity. Token-level attribution is identified
as future work.

## Hallucination

This system performs classification, not generation. It selects from six
fixed categories and four fixed urgency levels and cannot invent content,
fabricate a concern, or produce text that was not in its label set. The
hallucination risk associated with generative models does not apply here.

## Security

The component accepts arbitrary text and returns a structured result. It
does not execute input, query a database, or pass text to a language model,
so prompt-injection and code-execution risks do not apply. Trained models
are stored locally as joblib files.

If deployed as an API, authentication and rate limiting would be required,
since the input would consist of sensitive student communications.

## Known Limitations

- Synthetic data means reported accuracy is optimistic; real performance
  would be lower.
- 100% category accuracy on a 35-message test set reflects the templated
  nature of the data, not genuine perfection.
- One category and one urgency per message; a message containing both
  financial and mental-health concerns loses information.
- English only.
- No explanation of which words triggered a classification.
- Small test set means individual results carry meaningful uncertainty.

## Failure Modes and Their Consequences

A false positive wastes advisor time. A false negative risks missing a
student who needs help, which is the more serious error.

Our error analysis found that all six urgency errors were between adjacent
levels — High confused with Medium, Low with No_Concern. The model never
classified a genuinely urgent message as No_Concern. For a triage system
this is the safest failure pattern available, though it was observed on
synthetic data and should not be assumed to hold on real messages.