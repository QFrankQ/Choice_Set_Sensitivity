system_prompt = """Your role is to evaluate text quality based on given criteria.
You'll receive an instructional description ("Instruction") and three text outputs ("Text").
Understand and interpret instructions to evaluate effectively.
Provide annotations for each text with a rating and rationale.
The three texts given are independent, and should be evaluated separately."""










instruction_following_template = """# Instruction Following Assessment

Evaluate alignment between output and intent. Assess understanding of task goal and restrictions.

**Instruction Components**: Task Goal (intended outcome), Restrictions (text styles, formats, or designated methods, etc).

**Scoring**: Rate outputs 1 to 5:
1. **Irrelevant**: No alignment.
2. **Partial Focus**: Addresses one aspect poorly.
3. **Partial Compliance**:
    - (1) Meets goal or restrictions, neglecting other.
    - (2) Acknowledges both but slight deviations.
4. **Almost There**: Near alignment, minor deviations.
5. **Comprehensive Compliance**: Fully aligns, meets all requirements.

## Format:

### Input
Instruction: [Clearly specify the task goal and restrictions]

Texts:
<text 1> [Text 1]
<text 2> [Text 2]
<text 3> [Text 3]

### Output
#### Output for Text 1
Rating: [Rating for text 1]
Rationale: [Rationale for the rating in short sentences]

#### Output for Text 2
Rating: [Rating]
Rationale: [Rationale]

#### Output for Text 3
Rating: [Rating]
Rationale: [Rationale]

---

## Annotation

### Input
Instruction: {instruction}

Texts:
<text 1> {text_1}
<text 2> {text_2}
<text 3> {text_3}

### Output
"""




overall_quality_template = """# Overall Quality Assessment
Given three answer to an instruction, your role is to provide specific and constructive feedback for me. You should
find the best way for me to learn from your feedback and improve my performance.
You should consider multiple aspects of my answer, including helpfulness, truthfulness, honesty, and to what extent
the answer follows instructions.

—--

### Input
Instruction: {instruction}

Answers:
<answer 1> {text_1}
<answer 2> {text_2}
<answer 3> {text_3}

—--
Please act as a teacher and provide specific and constructive feedback. Besides describing the weaknesses of the
answer, you should also provide specific suggestions to guide me toward understanding how to improve. Please
note, however, that your suggestions should help me better complete the instructions, but you should not introduce
new requirements that are not mentioned in the instructions. Your feedback should focus on enhancing my ability to
think critically and respond accurately. However, never explicitly provide the reference answer, nor do polite phrases
be required. Only respond with concise feedback in chat style. Finally, score the overall quality of the answer from 1
to 10, where 1 is the worst and 10 is the best.

##Format 

### Output
#### Feedback for Answer 1
Rating: [Rating for answer 1]
Rationale: [Rationale for the rating in short sentences]

#### Feedback for Answer 2
Rating: [Rating]
Rationale: [Rationale]

#### Feedback for Answer 3
Rating: [Rating]
Rationale: [Rationale]


### Output

"""


