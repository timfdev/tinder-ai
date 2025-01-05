POST /api/generate/opener
- Purpose: Generate an engaging opening message based on profile info
- Input: {
    profile: {
        name: string,
        age: number,
        bio: string | null,
        interests: string[] | null
    }
}
- Output: {
    message: string,
    context?: string  // Optional context about why this message was chosen
}

POST /api/generate/reply
- Purpose: Generate contextual reply to a received message
- Input: {
    profile: {
        name: string
    },
    last_message: string,
    last_messages?: string[]  // Optional, last few messages for context
}
- Output: {
    message: string,
    context?: string
}