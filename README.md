## Guidelines
**[Assignment 1 PDF Guide](./CC_Fall2025_Assignment1.pdf)**

### 1. Upload files to GitHub & create a release

- Upload your code to GitHub. Your repo should contain 3 folders (front-end, lambda-functions and other-scripts)  
- Create a release on GitHub.

### 2. Video Recording (3–5 minutes max)

- Record one continuous, unedited screen recording (no cuts, no editing) of your end to end workflow. No voice over required.  
- Upload the video as Unlisted on YouTube.

### 3. What to Show in the Video

- **Albert Profile** – Show one team member’s Albert profile for 2–3 seconds.  
- **AWS Resources** – Open multiple browser tabs in advance (Lambda, Opensearch, API Gateway, Lex, SQS, DynamoDB, etc). For each tab, quickly scroll through your configurations/code (3–5 seconds each). No need to show any curl commands or data-loading scripts you used.  
- **Chatbot Demo** – Start a conversation with your chatbot and complete the flow. Example: greeting, request restaurant suggestions, provide location, cuisine, email, etc. Show proper exception handling (In case of invalid locations, cuisine, etc.)  
- **Email Verification** – Open your inbox and show the new email is generated with 3-4 restaurant suggestions based on your conversation with the Chatbot.  
- **CloudWatch/EventBridge** – Go to the trigger page in your aws console, and show that it is invoking your LF2.  
- **Extra Credit (Optional)** – If you have done the extra credit, simulate a failure and show that the message is moved to DLQ and the failure is logged in CloudWatch.

Please do all this in a single recording and don’t waste time in editing it. The quick, precise and unedited the video, the better it is. We will check your code and this video to grade the assignment.  

**PLEASE UPLOAD YOUTUBE VIDEOS ONLY**

### 4. Brightspace submission

- Upload the GitHub release (code).  
- The repo url  
- YouTube video link


## Instructions

### Code Repository Setup

- Maintain all your code in a GitHub repository.  
- Commit your code regularly so that the commit history is visible and meaningful.

### Repository Structure

Your repository must contain three folders:

- `frontend/`  
- `lambda-functions/`  
- `other-scripts/`  

### Release Creation

- Create a release on GitHub.  
- Upload a ZIP file of your final submission as part of the release.

### Demo Video

Record and submit a video demonstration of your end-to-end workflow.

The demo should:

- Begin with your NYU Albert Profile screen (with your username clearly visible).  
- Show a working chat demo.  
- Walk through all resources created as part of Assignment 1.

### Submission Rules

- One submission per team.  
- **Max Team Size:** 2  

**NOTE:**  

- Be mindful of your cloud resource usage.  
- Ensure there are no orphan resources left running.  
- Decommission all resources once your assignment is completed.
