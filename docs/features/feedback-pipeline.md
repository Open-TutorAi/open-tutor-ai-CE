# Feedback Pipeline

The feedback pipeline is a core feature of Open Tutor AI that enables systematic evaluation and improvement of AI responses through both student and teacher feedback.

## Overview

The feedback pipeline consists of two main types of feedback:

1. **Student Feedback**: Direct feedback from students on AI responses
2. **Teacher Feedback**: Pedagogical evaluation of paired AI responses

## Student Feedback

### Collection Process
- Students can provide feedback on any AI response
- Feedback includes:
  - Rating (1-5 stars)
  - Reason for rating
  - Optional comments
  - Timestamp

### Storage
```typescript
interface StudentFeedback {
  rating: number;
  reason: string;
  comment: string;
  timestamp: number;
  message_id: string;
}
```

### Usage
- Used to improve AI response quality
- Helps identify patterns in student preferences
- Provides data for model fine-tuning

## Teacher Feedback

### Collection Process
- Teachers evaluate pairs of AI responses to the same question
- Each evaluation includes:
  - Selection of preferred response
  - Pedagogical reasoning
  - Timestamp
  - Question context

### Storage
```typescript
interface TeacherFeedback {
  preferredResponseId: string;
  reason: string;
  timestamp: number;
  questionId: string;
  question: string;
  responses: {
    id: string;
    content: string;
    modelName: string;
  }[];
}
```

### Usage
- Guides AI model improvements
- Provides pedagogical insights
- Helps maintain teaching standards
- Supports curriculum development

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

## Technical Implementation

### Data Flow
1. Chat messages are processed to identify pairs
2. Student feedback is collected and stored
3. Teacher evaluations are recorded
4. Data is used for model improvement

### API Endpoints
- `GET /api/v1/chats/all/db` - Fetch all chats
- `GET /api/v1/feedbacks/all` - Fetch all feedbacks
- `POST /api/v1/response-feedbacks` - Submit teacher evaluation

### Security
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
- Automated feedback analysis
- Integration with learning management systems
- Advanced filtering and search capabilities
- Feedback analytics dashboard

## Related Documentation
- [API Reference](../api/feedback-api.md)
- [User Guide](../user-guide/feedback.md)
- [Admin Guide](../admin/feedback-management.md)