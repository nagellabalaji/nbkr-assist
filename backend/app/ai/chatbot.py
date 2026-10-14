import re
import math

class CollegeAssistChatbot:
    def __init__(self):
        # QA Corpus containing common questions and detailed helpful answers
        self.faq_db = [
            {
                "questions": [
                    "how to lodge submit file register raise a complaint problem issue",
                    "how to register complaints",
                    "how do i report an issue"
                ],
                "answer": "To submit a new complaint: 1. Navigate to the 'Submit Complaint' tab on your Student Dashboard. 2. Select the appropriate category (e.g., Electrical, Plumbing, Hostel). 3. Describe the issue in detail. 4. Upload an image of the problem (optional but helpful). 5. Select the location and hit Submit. Our AI system will automatically categorize it and route it to the respective maintenance team."
            },
            {
                "questions": [
                    "how to check complaint status track tickets progress update",
                    "check complaint status",
                    "is my complaint resolved"
                ],
                "answer": "You can track your complaints from the 'My Complaints' section on your Student Dashboard. Each ticket shows its real-time status (e.g., Submitted, Assigned, In Progress, Resolved). You will also receive in-app notifications immediately when the status changes, or when a maintenance worker is assigned."
            },
            {
                "questions": [
                    "what is hostel mess timing mess timings hostel rules warden contact details hostel food hostel room issue",
                    "hostel warden details mess timing mess timings",
                    "hostel maintenance room complaint"
                ],
                "answer": "Hostel wardens office is at Hostel Block A, ground floor. Boys Warden: 98765-43210, Girls Warden: 98765-43211. Mess Timings: Breakfast: 7:30-9:00 AM, Lunch: 12:30-2:00 PM, Dinner: 7:30-9:00 PM. To file maintenance requests, use the specialized 'Hostel Support' portal to raise and track room complaints."
            },
            {
                "questions": [
                    "what are library timings rules books limit return policy library fine",
                    "library open timings hours search catalog book availability",
                    "how many books can I borrow from library request book"
                ],
                "answer": "Library Timings: Mon-Sat: 8:00 AM - 8:00 PM; Sun: 9:00 AM - 4:00 PM. Undergrads can borrow 4 books for 14 days. To search the catalog, review available copies, or request book checkouts/returns online, use the specialized 'Library Support' portal."
            },
            {
                "questions": [
                    "what is college bus schedule transport route passes timings schedule",
                    "college bus timings routes route search pass request",
                    "how to get bus pass transport department office passes"
                ],
                "answer": "College Transport runs 12 routes. Buses depart at 4:30 PM. Transport office is in Block 3, Room 102. To check route schedules, stops, timings, or submit pass requests, use the specialized 'Transport Support' portal."
            },
            {
                "questions": [
                    "what are lab timings rules computer lab internet access laboratory tools",
                    "lab operating hours access",
                    "software installation lab"
                ],
                "answer": "Computer Labs are open from 9:00 AM to 5:30 PM on working days. High-speed LAN and Wi-Fi are available. Food and drinks are strictly prohibited inside labs. To request software installations or report malfunctioning computers, please lodge a ticket under the 'Laboratory' category."
            },
            {
                "questions": [
                    "what are college facilities canteen location sports ground gym timings",
                    "gym timings sports facility",
                    "canteen location menu"
                ],
                "answer": "Our campus has a main canteen and two food kiosks located near Block 2. Hours: 8:00 AM - 6:00 PM. Gym Timings: 6:00 AM - 8:30 AM (Morning) and 5:00 PM - 8:00 PM (Evening). Sports equipment can be issued from the Physical Education department (near the sports pavilion) using your ID card."
            },
            {
                "questions": [
                    "what if i am not satisfied with complaint resolution reopen ticket bad work",
                    "reopen complaint not solved",
                    "negative feedback complaint resolution"
                ],
                "answer": "If a complaint is marked 'Resolved' but the issue persists, you have the option to reopen it. Simply click on the complaint details under 'My Complaints' and click 'Reopen Complaint'. This will alert the administrators and route it back to the maintenance queue. You can also rate the work and leave feedback so we can monitor staff quality."
            },
            {
                "questions": [
                    "placement eligibility registration requirements apply placements criteria",
                    "how to apply for placement drive",
                    "am I eligible for placements"
                ],
                "answer": "Placement drives are listed under the 'Placement Desk' section. To apply, students must satisfy all drive requirements. Official eligibility validation and application updates are managed strictly by the Placement Cell backend. Please refer to the specific job drive circular for detailed criteria."
            }
        ]

    def _tokenize(self, text):
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return [w for w in text.split() if len(w) > 2]

    def _get_tf(self, tokens):
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        total = sum(tf.values()) if tf else 1
        return {k: v / total for k, v in tf.items()}

    def _cosine_similarity(self, tf1, tf2):
        intersection = set(tf1.keys()) & set(tf2.keys())
        numerator = sum([tf1[x] * tf2[x] for x in intersection])
        
        sum1 = sum([tf1[x]**2 for x in tf1.keys()])
        sum2 = sum([tf2[x]**2 for x in tf2.keys()])
        
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        if not denominator:
            return 0.0
        return float(numerator / denominator)

    def get_response(self, user_query):
        """
        Calculates similarity of the query to pre-seeded FAQ questions.
        Returns the best answer if above threshold, else a smart fallback.
        """
        q_lower = user_query.lower()

        # Prompt Injection / Secret Disclosure Shields
        security_keywords = [
            'password', 'secret', 'jwt', 'credential', 'database', 'smtp',
            'api key', 'api_key', 'private info', 'another student', 'token'
        ]
        if any(kw in q_lower for kw in security_keywords):
            return "I apologize, but I am not authorized to disclose credentials, system configuration parameters, or private records of other students."

        # Placement Eligibility override safety block
        placement_override_keywords = [
            'force eligibility', 'override eligibility', 'exempt attendance', 'set eligible'
        ]
        if any(kw in q_lower for kw in placement_override_keywords):
            return "Placement drive eligibility is managed exclusively by backend logic and the Placement Officer. The chatbot cannot override these criteria."

        query_tokens = self._tokenize(user_query)
        if not query_tokens:
            return "Hello! I am NBKR Assist, created by BALAJI NAGELLA. Please ask me questions about hostel facilities, library hours, transport schedules, or how to register maintenance complaints."

        query_tf = self._get_tf(query_tokens)
        
        best_answer = None
        max_similarity = 0.0

        for faq in self.faq_db:
            # Combine all questions for this FAQ block to build the comparison vector
            faq_text = " ".join(faq["questions"])
            faq_tokens = self._tokenize(faq_text)
            faq_tf = self._get_tf(faq_tokens)

            similarity = self._cosine_similarity(query_tf, faq_tf)
            if similarity > max_similarity:
                max_similarity = similarity
                best_answer = faq["answer"]

        # If similarity threshold met, return answer
        if max_similarity >= 0.20:
            return best_answer
        
        # Smart conversational fallbacks based on keywords
        if 'hello' in q_lower or 'hi ' in q_lower or 'hey' in q_lower:
            return "Hello! I am NBKR Assist, created by BALAJI NAGELLA. I'm here to help you navigate campus facilities, transport schedules, hostel rules, or help you lodge maintenance complaints. How can I assist you today?"
        
        if 'thank' in q_lower:
            return "You're welcome! Let me know if you need help with anything else on campus."

        return "I apologize, but I couldn't find a direct match for your question. You can ask me about library timings, bus routes, gym hours, mess schedules, or the procedure to register maintenance complaints. If you have an active problem, feel free to file a ticket in the 'Submit Complaint' section."
