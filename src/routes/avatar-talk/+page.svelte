<script lang="ts">
    import { onMount } from 'svelte';
    import AvatarChat from '$lib/components/chat/AvatarChat.svelte';
    import { settings } from '$lib/stores';
    import { generateChatCompletion } from '$lib/apis/ollama';


    // State for classroom settings
    let useClassroom = true;
    let classroomModel: 'default' | 'alternative' = 'default';
    let userInput = '';
    let currentMessage = ''; // Start with empty message
    let speaking = false;
    let isLoading = false;
    
    onMount(() => {
        // Set the selected avatar ID in settings if not already set
        if (!($settings as any)?.selectedAvatarId) {
            settings.update(s => {
                return { ...s, selectedAvatarId: 'The Scholar' };
            });
        }

        // Set a welcome message when component mounts
        currentMessage = 'Welcome to the classroom! I am your AI tutor. What would you like to learn about today?';
    });

    // Toggle classroom visibility
    function toggleClassroom() {
        useClassroom = !useClassroom;
    }

    // Toggle classroom model
    function toggleClassroomModel() {
        classroomModel = classroomModel === 'default' ? 'alternative' : 'default';
    }

       // Helper function to extract response from JSON if needed
       function extractResponseFromJson(content: string): string {
        if (typeof content !== 'string') {
            return content || '';
        }
        
        // Direct regex extraction of "response" field
        // This is a fallback approach that directly looks for the response pattern we see in screenshots
        const directResponseMatch = content.match(/"response"\s*:\s*"([^"]+)"/);
        if (directResponseMatch && directResponseMatch[1]) {
            console.log("Found response via direct pattern matching:", directResponseMatch[1]);
            return directResponseMatch[1];
        }
        
        // Check if the content starts with ```json (markdown code block)
        if (content.trim().startsWith('```json') || content.includes('```json')) {
            console.log("Found markdown code block with JSON");
            // Try different patterns to extract the JSON content
            let jsonText = '';
            
            // Pattern 1: Standard markdown code block
            const codeBlockMatch = content.match(/```json\s*([\s\S]*?)```/);
            if (codeBlockMatch && codeBlockMatch[1]) {
                jsonText = codeBlockMatch[1].trim();
            } 
            // Pattern 2: If the closing ``` is missing
            else if (content.includes('```json')) {
                jsonText = content.split('```json')[1].trim();
            }
            
            if (jsonText) {
                console.log("Extracted JSON from code block:", jsonText);
                try {
                    const parsedJson = JSON.parse(jsonText);
                    if (parsedJson.response) {
                        console.log("Found response field:", parsedJson.response);
                        return parsedJson.response;
                    }
                } catch (e) {
                    console.error('Error parsing JSON code block:', e);
                }
            }
        }
        
        // Check if it looks like JSON
        if (content.trim().startsWith('{') && content.trim().endsWith('}')) {
            try {
                const parsedJson = JSON.parse(content);
                if (parsedJson.response) {
                    return parsedJson.response;
                }
            } catch (e) {
                console.error('Error parsing JSON content:', e);
            }
        }
        
        return content;
    }
    // Send message to LLM and get response
    async function sendMessage() {
        if (!userInput.trim() || isLoading) return;
        
        isLoading = true;
        
        try {
            // Get token from localStorage
            const token = localStorage.getItem('token');
            
            if (!token) {
                console.error('No authentication token available');
                currentMessage = 'Error: Not authenticated. Please log in.';
                return;
            }
            
            // Call the API
            const messageData = {
                model: ($settings as any)?.defaultModel || 'llama3',
                messages: [
                    {
                        role: 'system',
                        content: 'You are an AI tutor in a classroom setting. Provide clear, educational responses.'
                    },
                    {
                        role: 'user',
                        content: userInput
                    }
                ],
                stream: false
            };
            
            // The API returns [response, controller]
            const [response, controller] = await generateChatCompletion(token, messageData);
            
            if (response && 'ok' in response && response.ok) {
                // Parse the JSON response
                const responseData = await response.json();
                
                // Display the response on the board
                if (responseData.choices && responseData.choices[0] && responseData.choices[0].message) {
                    const messageContent = responseData.choices[0].message.content;
                    
                    // Process the message content to extract just the response
                    currentMessage = extractResponseFromJson(messageContent);
                    speaking = true;
                } else {
                    currentMessage = 'I received your question but encountered an unexpected response format.';
                }
            } else {
                currentMessage = 'I apologize, but I encountered an issue processing your request.';
            }
        } catch (error) {
            console.error('Error sending message:', error);
            currentMessage = 'I apologize, but I encountered an error. Please try again.';
        } finally {
            isLoading = false;
            userInput = ''; // Clear input field
        }
    }

</script>

<div class="h-full flex flex-col">
    <div class="flex justify-between items-center p-4 bg-gray-800 text-white">
        <h1 class="text-xl font-bold">Virtual Classroom Experience</h1>
        <div class="flex gap-4">
            <button 
                class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
                on:click={toggleClassroom}
            >
                {useClassroom ? 'Avatar Only View' : 'Classroom View'}
            </button>
            {#if useClassroom}
                <button 
                    class="px-4 py-2 bg-green-600 rounded hover:bg-green-700"
                    on:click={toggleClassroomModel}
                >
                    {classroomModel === 'default' ? 'Modern Classroom' : 'Traditional Classroom'}
                </button>
            {/if}
        </div>
    </div>
    
    <div class="flex-1 relative overflow-hidden bg-gray-900">
        <AvatarChat 
            className="w-full h-full" 
            {useClassroom}
            {classroomModel}
            {currentMessage}
            {speaking}
        />
    </div>

    <div class="bg-gray-800 p-4">
        <div class="max-w-4xl mx-auto flex gap-2">
            <input
                type="text"
                bind:value={userInput}
                placeholder="Ask any question..."
                class="flex-1 px-4 py-2 rounded bg-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                on:keydown={e => e.key === 'Enter' && sendMessage()}
                disabled={isLoading}
            />
            <button
                class="px-6 py-2 bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
                on:click={sendMessage}
                disabled={isLoading}
            >
                {isLoading ? 'Thinking...' : 'Ask'}
            </button>
        </div>
    </div>
    
    {#if useClassroom}
    <div class="p-2 bg-gray-700 text-white text-sm text-center">
        You're experiencing a virtual classroom with your AI tutor standing at the board. The view is from a student sitting in the front-row desk.
    </div>
    {/if}
</div>

<style>
    :global(body) {
        background-color: #1a202c;
        color: white;
        margin: 0;
        padding: 0;
        height: 100vh;
        overflow: hidden;
    }
</style>
