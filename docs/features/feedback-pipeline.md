# Feedback Pipeline

The feedback pipeline is a core feature of Open Tutor AI that enables systematic evaluation and improvement of AI responses through both student and teacher feedback.

## Overview

The feedback pipeline consists of two main types of feedback:

1. **Student Feedback**: Direct feedback from students on AI responses
2. **Teacher Feedback**: Pedagogical evaluation of paired AI responses

## Student Feedback

### Collection Process
- Students can provide feedback on any Tutor response
- Feedback includes:
  - Rating 
  - Reason for rating
  - Optional comments
  - Timestamp


## Teacher Feedback

### Collection Process
- Teachers evaluate pairs of Tutor responses to the same question
- Teachers Provide pedagogical evaluation basing on the Tutore Reseponses quality and student feedback
- Each evaluation includes:
  - Selection of preferred response
  - Student feedback (if available)
  - Pedagogical reasoning
  - Timestamp
  - Question context


## Usage
- Used to improve AI response quality
- Helps identify patterns in student preferences
- Provides pedagogical insights
- Helps maintain teaching standards
- Supports curriculum development
- Provides data for model fine-tuning


## Feedback Interface

### Teacher View
- Access to all paired responses
- Filtering options:
  - All pairs
  - To Do (unevaluated)
  - Done (evaluated)
- Statistics display:
  - Total pairs
  - Evaluated pairs
  - Progress percentage

### Evaluation Process
1. View question and paired responses
2. Review student feedback (if available)
3. Select preferred response
4. Provide pedagogical reasoning
5. Submit evaluation

## Security
- Teacher authentication required
- Role-based access control
- Data validation and sanitization

## Best Practices

### For Teachers
- Provide detailed pedagogical reasoning
- Consider both student feedback and teaching objectives
- Regular evaluation of new pairs
- Focus on educational value

### For Students
- Provide honest and constructive feedback
- Include specific reasons for ratings
- Use comments to elaborate on feedback

## Future Improvements
- Add correction mechanismes to correcte AI generated responses
- Advanced filtering and search capabilities
- Improve Admin Feedback analytics dashboard

