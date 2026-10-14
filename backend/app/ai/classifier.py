import re
import math

class LocalNLPClassifier:
    def __init__(self):
        # 10 Official categories and keyword anchors
        self.categories_corpus = {
            'Academic': [
                "faculty behavior teaching attendance shortage lectures timetable schedule subject assignment marks internal marks laboratory coursework lab record assignment submit"
            ],
            'Exam Cell': [
                "hall ticket admit card exam timetable schedules results cgpa gpa revaluation supplementary exam mark list correction duplicate hallticket"
            ],
            'Placement': [
                "placement drive company recruit mock interview training resume review internship registration offer letter packaging packages salary eligibility criteria recruitment"
            ],
            'Hostel': [
                "hostel room cupboard warden mess food hygiene dining hall water supply hot water electricity internet connection room clean roommate issues geyser room key"
            ],
            'Transport': [
                "college bus bus route timings delay passes pass counter driver rash driving entry card vehicle parking shuttle facility travel bus timing"
            ],
            'Library': [
                "library book book issue return card borrow renewal reading room silence access digital library reference book not available dues fine"
            ],
            'Maintenance': [
                "electrical plumbing furniture broken desk chair fan light ac remote projector remote glass cracked whiteboard classroom ceiling leak washroom tap infrastructure switch socket"
            ],
            'IT / Wi-Fi': [
                "wifi connection lan port login portal internet speed bandwidth limit authentication network error offline disconnect browser server down credentials"
            ],
            'Student Support': [
                "student grievance cell support counseling scholarship fee delay refund anti ragging discipline council mentor counseling harassment support desk"
            ],
            'General': [
                "canteen sports ground security gate pass general query admin block documents fee counter certificate duplicate id card office enquiry"
            ]
        }

        # Subcategories keyword dictionary
        self.subcategories = {
            'Academic': {
                'Faculty': ['faculty', 'teacher', 'professor', 'lecture', 'teaching'],
                'Attendance': ['attendance', 'present', 'absent', 'shortage', 'percentage', 'condonation'],
                'Timetable': ['timetable', 'schedule', 'hour', 'class timing', 'period'],
                'Subject': ['subject', 'syllabus', 'course', 'elective'],
                'Assignment': ['assignment', 'submission', 'submit', 'deadline'],
                'Laboratory': ['laboratory', 'lab', 'practical', 'experiment', 'record', 'viva'],
                'Internal Marks': ['internal', 'marks', 'midterm', 'mid', 'assessment']
            },
            'Exam Cell': {
                'Hall Ticket': ['hall ticket', 'hallticket', 'admit card', 'registration card'],
                'Exam Timetable': ['timetable', 'schedule', 'exam date', 'exam timing'],
                'Results': ['result', 'marksheet', 'gpa', 'cgpa', 'grade', 'failed', 'passed'],
                'Revaluation': ['revaluation', 'reval', 'recounting', 'paper verification'],
                'Supplementary Exam': ['supplementary', 'backlog', 'supply', 'exam fee', 'arrear']
            },
            'Placement': {
                'Placement Drive': ['placement drive', 'recruitment', 'company', 'wipro', 'tcs', 'cognizant', 'infosys', 'drive date'],
                'Training': ['training', 'aptitude', 'coding class', 'skills', 'mock test'],
                'Internship': ['internship', 'noc', 'industry training', 'stipend'],
                'Interview': ['interview', 'gd', 'group discussion', 'hr round'],
                'Resume Support': ['resume', 'cv', 'portfolio', 'bio-data']
            },
            'Hostel': {
                'Room': ['room', 'cupboard', 'wardrobe', 'bed', 'mattress', 'key', 'lock', 'roommate'],
                'Food': ['food', 'mess', 'hygiene', 'taste', 'quality', 'caterer', 'breakfast', 'dinner'],
                'Water': ['water', 'drinking water', 'geyser', 'hot water', 'cooler'],
                'Electricity': ['electricity', 'power cut', 'no power', 'plug', 'generator'],
                'Internet': ['internet', 'wifi', 'wi-fi', 'router', 'slow connection'],
                'Cleanliness': ['clean', 'sweeping', 'dirty', 'dustbin', 'corridor', 'housekeeping']
            },
            'Transport': {
                'Bus Route': ['route', 'bus route', 'area', 'stop', 'pickup'],
                'Bus Timing': ['timing', 'delay', 'schedule', 'timing change', 'late'],
                'Driver': ['driver', 'cleaner', 'rash', 'behavior', 'speeding'],
                'Bus Pass': ['pass', 'bus pass', 'counter', 'fee', 'renewal'],
                'Vehicle': ['vehicle', 'car', 'bike', 'parking', 'garage', 'repair']
            },
            'Library': {
                'Book': ['book', 'author', 'title', 'journal', 'magazine'],
                'Availability': ['availability', 'not available', 'out of stock', 'missing'],
                'Issue/Return': ['issue', 'return', 'fine', 'due date', 'renew', 'borrow'],
                'Library Access': ['access', 'card', 'id card', 'digital library', 'entry time']
            },
            'Maintenance': {
                'Electrical': ['electrical', 'fan', 'light', 'tube light', 'bulb', 'switch', 'sparking', 'short circuit', 'current', 'wire'],
                'Plumbing': ['plumbing', 'leak', 'water leakage', 'tap', 'flush', 'toilet', 'pipe', 'clogged', 'drain'],
                'Furniture': ['furniture', 'desk', 'chair', 'bench', 'podium', 'door', 'window', 'cupboard'],
                'AC/Fan': ['ac', 'fan', 'regulator', 'cooling', 'blower', 'air conditioner'],
                'Projector': ['projector', 'remote', 'display', 'hdmi', 'screen', 'vga'],
                'Classroom': ['classroom', 'whiteboard', 'marker', 'speaker', 'podium mic'],
                'Infrastructure': ['infrastructure', 'ceiling', 'floor', 'tile', 'paint', 'wall', 'corridor']
            },
            'IT / Wi-Fi': {
                'Internet': ['internet', 'slow', 'online', 'bandwidth', 'disconnect'],
                'Wi-Fi': ['wifi', 'wi-fi', 'router', 'signal', 'range'],
                'Computer': ['computer', 'monitor', 'mouse', 'keyboard', 'system', 'desktop'],
                'Software': ['software', 'installation', 'license', 'os', 'visual studio', 'eclipse'],
                'Network': ['network', 'lan', 'port', 'ethernet', 'switch', 'firewall']
            },
            'Student Support': {
                'General': ['support', 'scholarship', 'refund', 'counseling', 'mentor', 'ragging']
            },
            'General': {
                'General': ['general', 'query', 'canteen', 'sports', 'id card', 'office']
            }
        }

        # Department routing map based on category
        self.department_map = {
            'Academic': 'Academic Administration',
            'Exam Cell': 'Exam Section Management',
            'Placement': 'Corporate Relations',
            'Hostel': 'Hostel Administration',
            'Transport': 'Transport Department',
            'Library': 'Library Services',
            'Maintenance': 'Estates Maintenance',
            'IT / Wi-Fi': 'IT & Network Support',
            'Student Support': 'Student Support Cell',
            'General': 'General Administration'
        }

        # Urgency keywords dictionary
        self.urgency_keywords = {
            'Urgent': ['shock', 'fire', 'spark', 'smoke', 'burst', 'flood', 'blast', 'hazard', 'short-circuit', 'short circuit', 'current', 'exposed wire'],
            'High': ['leak', 'leakage', 'no water', 'broken', 'darkness', 'exam', 'exam room', 'no power', 'failed', 'blocked', 'choked', 'stink', 'smell', 'urgent'],
            'Medium': ['slow', 'not working', 'not loading', 'loose', 'noise', 'cracked', 'dirty', 'messy', 'full', 'dusty', 'stuck'],
            'Low': ['scratch', 'paint', 'missing', 'lost key', 'squeak', 'smudge', 'adjust']
        }

    def _tokenize(self, text):
        """Clean and split text into normalized words."""
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        return [w for w in text.split() if len(w) > 2]

    def _get_tf(self, tokens):
        """Compute Term Frequency (TF) dict."""
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        total = sum(tf.values()) if tf else 1
        return {k: v / total for k, v in tf.items()}

    def _cosine_similarity(self, tf1, tf2):
        """Compute Cosine Similarity between two term frequency dictionaries."""
        intersection = set(tf1.keys()) & set(tf2.keys())
        numerator = sum([tf1[x] * tf2[x] for x in intersection])
        
        sum1 = sum([tf1[x]**2 for x in tf1.keys()])
        sum2 = sum([tf2[x]**2 for x in tf2.keys()])
        
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        
        if not denominator:
            return 0.0
        return float(numerator / denominator)

    def classify_complaint(self, description):
        """
        Classifies the complaint category, subcategory, priority, department, and action.
        Returns a tuple: (category, subcategory, priority, suggested_department, suggested_action, confidence)
        """
        desc_tokens = self._tokenize(description)
        if not desc_tokens:
            return 'General', 'General', 'Medium', 'General Administration', 'Forward to Admin Office', 0.1

        desc_tf = self._get_tf(desc_tokens)
        desc_lower = description.lower()

        # 1. Category Classification via Cosine Similarity
        best_category = 'General'
        max_similarity = 0.0

        for category, documents in self.categories_corpus.items():
            category_text = " ".join(documents)
            cat_tokens = self._tokenize(category_text)
            cat_tf = self._get_tf(cat_tokens)

            similarity = self._cosine_similarity(desc_tf, cat_tf)
            if similarity > max_similarity:
                max_similarity = similarity
                best_category = category

        # Rule-based enhancements
        if 'wifi' in desc_lower or 'internet' in desc_lower or 'router' in desc_lower or 'network' in desc_lower or 'lan' in desc_lower:
            best_category = 'IT / Wi-Fi'
            max_similarity = max(max_similarity, 0.6)
        elif 'projector' in desc_lower or 'podium' in desc_lower or 'classroom' in desc_lower or 'fan' in desc_lower or 'light' in desc_lower or 'pipe' in desc_lower or 'leak' in desc_lower or 'leakage' in desc_lower:
            best_category = 'Maintenance'
            max_similarity = max(max_similarity, 0.5)
        elif 'exam' in desc_lower or 'results' in desc_lower or 'hall ticket' in desc_lower or 'hallticket' in desc_lower:
            best_category = 'Exam Cell'
            max_similarity = max(max_similarity, 0.5)
        elif 'placement' in desc_lower or 'resume' in desc_lower or 'interview' in desc_lower or 'recruit' in desc_lower:
            best_category = 'Placement'
            max_similarity = max(max_similarity, 0.5)
        elif 'bus' in desc_lower or 'transport' in desc_lower or 'route' in desc_lower:
            best_category = 'Transport'
            max_similarity = max(max_similarity, 0.5)
        elif 'library' in desc_lower or 'book' in desc_lower:
            best_category = 'Library'
            max_similarity = max(max_similarity, 0.5)
        elif 'mess' in desc_lower or 'warden' in desc_lower or 'hostel' in desc_lower:
            best_category = 'Hostel'
            max_similarity = max(max_similarity, 0.5)
        elif 'class' in desc_lower or 'faculty' in desc_lower or 'attendance' in desc_lower or 'internal' in desc_lower:
            best_category = 'Academic'
            max_similarity = max(max_similarity, 0.5)

        # 2. Subcategory Prediction
        best_subcategory = 'General'
        if best_category in self.subcategories:
            subcat_dict = self.subcategories[best_category]
            best_sub_score = -1
            best_subcategory = list(subcat_dict.keys())[0] # default to first subcategory
            
            for sub_name, keywords in subcat_dict.items():
                score = sum(1 for kw in keywords if kw in desc_lower)
                if score > best_sub_score:
                    best_sub_score = score
                    best_subcategory = sub_name

        # 3. Priority Prediction via Keyword Urgency Scans
        priority = 'Medium'
        urgent_matches = [w for w in self.urgency_keywords['Urgent'] if w in desc_lower or any(u in desc_lower for u in w.split())]
        high_matches = [w for w in self.urgency_keywords['High'] if w in desc_lower]
        medium_matches = [w for w in self.urgency_keywords['Medium'] if w in desc_lower]
        low_matches = [w for w in self.urgency_keywords['Low'] if w in desc_lower]

        if urgent_matches:
            priority = 'Urgent' # mapped to Critical on the front end or inside db
        elif high_matches:
            priority = 'High'
        elif low_matches and not medium_matches:
            priority = 'Low'
        else:
            priority = 'Medium'

        # Route to Department
        suggested_dept = self.department_map.get(best_category, 'General Administration')
        suggested_action = f"Assign to {suggested_dept} Staff"

        # Confidence calculation
        confidence = float(min(max_similarity * 2.0 + 0.1, 1.0))
        if max_similarity == 0.0:
            confidence = 0.2

        return best_category, best_subcategory, priority, suggested_dept, suggested_action, confidence

    def detect_duplicates(self, new_description, existing_complaints, threshold=0.75):
        """
        Compare new description with existing active complaints using cosine similarity.
        Returns a list of duplicate complaint dicts if similarity exceeds threshold.
        """
        new_tokens = self._tokenize(new_description)
        if not new_tokens:
            return []
        
        new_tf = self._get_tf(new_tokens)
        duplicates = []

        for comp in existing_complaints:
            comp_desc = comp.get('description', '')
            comp_tokens = self._tokenize(comp_desc)
            if not comp_tokens:
                continue
            
            comp_tf = self._get_tf(comp_tokens)
            similarity = self._cosine_similarity(new_tf, comp_tf)

            if similarity >= threshold:
                duplicates.append({
                    'id': comp.get('id'),
                    'title': comp.get('title'),
                    'status': comp.get('status'),
                    'created_at': comp.get('created_at'),
                    'similarity': round(similarity, 2)
                })

        return duplicates
