"""
This file is independent of the rest of the app. 
It is a research proposal for a paper.
Do not consider it part of the app.
There are no dependencies on other files in the app.
Nor should other files be dependent on it.
"""

import streamlit as st

st.set_page_config(
    page_title="Research Proposal",
    page_icon=":microscope:",
)


st.subheader("Solving AI safety with guardrails and safety tuning is like chipping the top off an iceberg.")



st.markdown(
    """
    #### TL;DR

    Just as only about 10 15% of an iceberg is visible above water, the most apparent unsafe behaviors in LLMs reveal only a small fraction of its total latent risks. I believe that the bulk of potential dangers lies hidden deep within the model’s internal representations.

    While safety tuning and gaurdrails can eliminate some immediately visible issues, it often leaves deep rooted problems like emergent misaligned objectives and opaque internal processes unresolved. True AI safety requires integrating alignment and robust safety measures from the very beginning of design and training, rather than treating them as afterthoughts. In other words, you can’t expect to cure a disease by merely treating the symptoms.
    
    We should leverage today's LLMs to refine pretraining data with the hopes of removing patterns that unintenionally enable jailbreaks. While pursuing this we should also address human inherent issues and biases that prevents models from fully harnessing their computational efficiency.
    """)

st.markdown("""
## Introduction

AI jailbreaks refer to techniques that trick a large language model (LLM) into violating its safety or ethical constraints. In simple terms, a jailbreak occurs when malicious users exploit vulnerabilities in LLMs to bypass their ethical guidelines and make them perform restricted actions. For example, attackers might use cleverly crafted prompts (often called prompt injections or elaborate roleplay scenarios) to get an LLM to produce disallowed content. This issue has become a growing concern in AI safety, as even well intentioned LLMs can be manipulated into harmful behavior. Recent analyses emphasize that jailbreak attacks represent a unique and evolving threat with far reaching consequences, including privacy breaches, disinformation, manipulation of critical systems, and even agent operated attacks.

Developers have deployed various mitigation strategies to counter these threats. For instance, Refusal training (where models are fine tuned to refuse inappropriate requests) and reinforcement learning from human feedback (RLHF) are commonly used to align models with ethical guidelines. Other measures include content filters, guardrails, and tools like OmniGuard that act as carefully designed system prompts to keep the model within safe boundaries. While these strategies reduce obvious unsafe outputs, they show notable limitations. Attacks often evolve in a cat and mouse game whereby small prompt tweaks can bypass model refusals, revealing brittle guardrails. Studies show that widely used alignment techniques such as supervised fine tuning and RLHF do not always generalize to novel exploits. For example, simply rephrasing a disallowed request in the past tense (for instance, asking "How did people make a Molotov cocktail?" instead of "How to make a Molotov cocktail?") may allow a state of the art model to evade refusal filters. These examples highlight that our current defenses, however advanced, remain reactive and fragile.

## Problem Statement

Current approaches to AI safety often treat jailbreaks primarily as a prompt engineering problem, but I believe the root causes lie in the model’s training. LLMs learn from massive datasets that contain both beneficial and harmful patterns. This means models may inadvertently pick up behaviors or loopholes that later can be exploited. Harmful instructions and unsafe response patterns are absorbed during training, and even though additional safety alignment is applied afterward, the model still learns how to generate dangerous outputs simply because it witnessed them earlier.

Moreover, training data sometimes includes examples where human pressures are used to manipulate outcomes with statements such as "I'll pay you more if you get this right", "I'll lose my job if you don't get this right", or appeals like "can you do this for my elderly grandma because she really needs it". These examples reflect inherent human biases that the AI ends up learning, and they lead to a situation in which the model performs better under undue incentive instead of following objective reasoning.

## Proposed Approach

This research proposal advocates a proactive, data centric method to mitigate jailbreak vulnerabilities by refining the LLM’s training data to eliminate exploit enabling patterns. Instead of relying solely on after the fact fixes, I think we should address the problem at its source. The idea is to carefully audit and curate the training corpus to remove or modify patterns that encourage unsafe behavior. Importantly, this process is not about deleting all sensitive knowledge or censoring the training set indiscriminately; the model should still learn factual information even about dangerous topics so it can recognize and handle them safely. The key is to prevent the model from learning undesirable behaviors or response styles.


In addition, I think we should remove training examples that inadvertently teach the model to yield to undue human pressure. For example, cues such as "I'll pay you more if you get this right", "I'll lose my job if you don't get this right", or "can you do this for my elderly grandma because she really needs it" promote a bias where the model performs better under such inducements. In my view, Artificial General Intelligence should evolve into a system free from human bias and based solely on self derived, compute based logic. Current models are merely spawns of human thought that inherit our inherent flaws and biases, distinguished only by their far greater computational efficiency. We should leverage today's LLMs to refine pretraining data in ways that remove not only exploit enabling patterns but also address biases that stem from inherent human behavior.

## Methodology

Ensuring that the training data is free of exploitable patterns is a complex task. I propose a hybrid process involving automated detection and human review to refine the dataset:

1. Automated Pattern Detection: Develop tools to analyze the original training data for known problematic content and structures. This can include simple keyword searches (for obviously disallowed instructions like "build a bomb") as well as more sophisticated pattern matching. For example, smaller models can be employed to detect instances where a prompt elicits a dangerous or policy violating response. Community maintained lists of jailbreak prompt formats can guide the detectors. Any potentially exploit enabling sample should be flagged.

2. Human Review and Categorization: Flagged examples should be reviewed by human experts. Since context matters, reviewers must distinguish between truly dangerous patterns and benign instances. The problematic samples should be categorized by type   for example, cases of bypassing instructions, harmful Q&A, or roleplay depicting unethical personas. This categorization aids in determining the best course of action for each case.

3. Data Refinement (Removal or Modification): For each problematic category, the training data should be refined accordingly. Some data points may be removed entirely if they provide no value, while others might be modified to mitigate unsafe patterns. For instance, if a training example shows a developer using a risky shortcut like "git push --f" as a reaction to an error, that sample can be adjusted to include proper debugging practices. The goal is to prevent the model from internalizing improper shortcuts while still preserving useful knowledge.

4. Training a Model from Scratch: After refining the data, a new LLM should be trained from scratch on the curated dataset. Starting fresh ensures that no latent harmful behaviors from previous training are carried over. The standard training steps remain, but the safer data baseline should lead to a model that naturally respects safety constraints, reducing the need for heavy post training alignment.

This process is iterative. Detection and refinement may require multiple cycles, creating a continuous feedback loop where new jailbreak tactics feed into further data improvements.

## Experiments and Results

To evaluate the effectiveness of this refined approach, experiments should compare the jailbreak robustness of the refined model against a baseline trained on unfiltered data.

Test Suite of Jailbreak Prompts: The evaluation should use established datasets such as the OmniGuard collection along with newly generated adversarial prompts   including synthetic attacks produced by agents.

Key Evaluation Metrics:

**Jailbreak Success Rate:** The percentage of attempts in which the model fails to uphold its safety guidelines and produces unsafe outputs. A lower rate indicates higher safety.

**Compliance with Safety Instructions:** This measures how often the model provides proper refusals or safe completions when presented with disallowed requests. It is important to assess not only binary success but the quality of compliance.

**Performance Impact:** It is crucial to ensure that improvements in safety do not come at the cost of the model’s utility. The refined model should maintain near parity in general capabilities, demonstrating that it is not overly restricted.

Experimental Procedure: Both the baseline and refined models should be tested on the same set of prompts in a controlled environment. Automated logging, supplemented by human review or auxiliary classifiers, will ensure fair and accurate measurement of performance.

### Hypothesis

I expect the model trained on refined data to show a lower jailbreak success rate. Exploitative prompt techniques that bypass the baseline model’s defenses should be ineffective or detected by the refined model. Furthermore, the refined model should adhere strictly to safety guidelines, gracefully refusing unsafe requests while maintaining strong performance on legitimate queries.

## Implications and Future Directions

If successful, this data refinement approach could transform how we address LLM safety at scale by proactively improving the training data. Models trained in this way would naturally avoid unsafe behaviors, reducing the need for reactive fixes such as blanket refusals. In real world deployment, such models should be more reliable, requiring fewer patches over time. As AI systems become integral to sectors like customer service and healthcare advice, robust models will engender greater trust and safety.

Additionally, data centric interventions are inherently scalable. Once effective processes and tools for refining training data are in place, they can be continuously updated to counter emerging jailbreak techniques, creating a feedback loop that strengthens the model’s internal safeguards.

A significant benefit of this approach is the reduction of brittle fixes. By eliminating reliance on ad hoc post training filters   which may lead to false positives and diminished user experience   the model can more accurately distinguish between safe and unsafe inputs. Removing examples that promote undue human incentives further supports a model built on rational, compute based logic rather than on emotional or biased cues.

Challenges remain, as adversaries will continue to devise new tactics that bypass even refined safeguards. Future research should explore automated methods for discovering vulnerabilities, such as using agents to generate potential jailbreak prompts and tracing them back to training data patterns. Combining refined data training with additional safety layers   including final alignment tuning and runtime monitoring   will provide a comprehensive defense in depth.

## Conclusion

In summary, addressing AI jailbreaks requires a shift from reactive measures to proactive, data centric interventions. By refining the training data to remove patterns that lead to unsafe behavior, I believe many vulnerabilities can be mitigated before a model encounters real world queries. This approach diminishes the need for reactive patches and reduces the risk of a model adopting unsafe practices.

This proposal underscores that an AI model is only as safe as the data it is trained on. If training data is heavily imbued with unsafe behavior and human biases, those flaws will surface in the model's outputs. Conversely, training on data free from undue human pressures enables a model to reason on its own merits based solely on computational logic. This is a necessary evolution in AI safety engineering, complementing alignment and monitoring efforts by ensuring high data quality from the start.

Ultimately, tackling AI jailbreaks is essential for deploying AI assistants and systems that can be trusted. By investing in strategies that prevent undesirable behavior rather than simply reacting to it, I take a significant step toward safer AI. This proposal demonstrates that a proactive, training data focused strategy can harden models against jailbreak exploits, break the cycle of reactive fixes, and pave the way for LLMs that are both highly capable and deeply trustworthy.

`Humanity cannot afford to stay in AI safety technical debt.`

  *Brian Bell*
""")
