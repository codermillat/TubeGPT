"""
Prompt templates with few-shot examples for YouTube analytics AI assistant.
Supports both English and Bengali with reusable template system.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class FewShotExample:
    """Structure for few-shot examples."""
    question: str
    answer: str
    context: Optional[str] = None

class PromptTemplateManager:
    """
    Manages prompt templates with few-shot examples for YouTube analytics.
    Supports both English and Bengali with contextual examples.
    """
    
    def __init__(self):
        self.templates = {
            'en': self._load_english_templates(),
            'bn': self._load_bengali_templates()
        }
    
    def _load_english_templates(self) -> Dict[str, List[FewShotExample]]:
        """Load English few-shot examples organized by category."""
        return {
            'ctr_analysis': [
                FewShotExample(
                    question="Which videos had the lowest CTR?",
                    answer="Your lowest CTR videos are:\n1. 'Cooking Tutorial Part 3' (0.8%) - 45K impressions\n2. 'Daily Vlog #127' (1.2%) - 32K impressions\n3. 'Tech Review: Budget Phone' (1.4%) - 28K impressions\n\nThese underperformed compared to your 3.2% average CTR. Consider updating thumbnails with brighter colors and clearer text.",
                    context="Low CTR indicates thumbnail/title issues"
                ),
                FewShotExample(
                    question="Why did my CTR drop last week?",
                    answer="Your CTR dropped from 4.1% to 2.8% last week. Analysis shows:\n\n• 3 videos used similar thumbnail styles (red background)\n• Upload timing shifted to 6 PM instead of usual 8 PM\n• Competition increased in your niche (5 similar videos published)\n\nRecommendation: Test different thumbnail styles and return to 8 PM uploads for better performance.",
                    context="CTR drops need multi-factor analysis"
                )
            ],
            
            'title_optimization': [
                FewShotExample(
                    question="Suggest better titles for my low-performing videos",
                    answer="Here are optimized title suggestions:\n\n**Current:** 'Cooking Rice'\n**Suggested:** 'Perfect Rice Every Time - 3 Secret Tips!' (adds urgency + benefit)\n\n**Current:** 'Phone Review'\n**Suggested:** 'This $200 Phone SHOCKED Me - Better Than iPhone?' (creates curiosity + comparison)\n\n**Current:** 'Travel Vlog'\n**Suggested:** 'I Spent 24 Hours in Bangladesh's Hidden Paradise' (specific + intriguing)\n\nFocus on emotional triggers, numbers, and clear benefits.",
                    context="Title optimization for engagement"
                ),
                FewShotExample(
                    question="What makes a good YouTube title?",
                    answer="Based on your top-performing videos, effective titles include:\n\n✅ **Numbers:** '5 Ways to...' (performs 40% better)\n✅ **Questions:** 'Why Does...' (increases curiosity)\n✅ **Emotional words:** 'Amazing', 'Shocking', 'Secret'\n✅ **Clear benefit:** What viewer will learn/gain\n✅ **Urgency:** 'Before It's Too Late', 'Right Now'\n\nYour best title: 'I Tried 7 Street Foods in Dhaka - #3 Will Shock You!' (847K views, 6.2% CTR)",
                    context="Title best practices from data"
                )
            ],
            
            'performance_trends': [
                FewShotExample(
                    question="What trends do you see in my video performance?",
                    answer="Key performance trends over the last 30 days:\n\n📈 **Improving:**\n• Average view duration: +15% (now 2:34 minutes)\n• Subscriber conversion: +22% (3.4% of viewers subscribe)\n• Weekend uploads perform 30% better\n\n📉 **Declining:**\n• CTR dropped 8% (from 4.2% to 3.9%)\n• Views from Bangladesh decreased 12%\n\n🎯 **Opportunities:**\n• Food content gets 2x more engagement\n• Videos 8-12 minutes long perform best\n• Thursday uploads have highest reach",
                    context="Comprehensive trend analysis"
                ),
                FewShotExample(
                    question="How is my channel growing compared to last month?",
                    answer="Channel growth comparison (This month vs Last month):\n\n**📊 Overall Performance:**\n• Total views: 1.2M (+18%) ⬆️\n• Average CTR: 3.9% (-0.3%) ⬇️\n• Watch time: 45K hours (+25%) ⬆️\n\n**🎯 Top Improvements:**\n• 'Street Food Series' gained 340K views (+89%)\n• Comment engagement up 45%\n• Shares increased by 67%\n\n**⚠️ Areas to Focus:**\n• 3 videos underperformed (below 10K views)\n• CTR needs attention - test new thumbnail styles\n• Upload consistency: only 12 videos vs target 16",
                    context="Month-over-month growth analysis"
                )
            ],
            
            'audience_insights': [
                FewShotExample(
                    question="Tell me about my audience demographics",
                    answer="Your audience analysis:\n\n**🌍 Geographic Distribution:**\n• Bangladesh: 68% (primary audience)\n• India: 15% (growing segment)\n• USA: 8% (high engagement)\n• UK: 5%, Others: 4%\n\n**📱 Device Usage:**\n• Mobile: 82% (optimize for mobile viewing)\n• Desktop: 15%, TV: 3%\n\n**⏰ Peak Activity:**\n• Best upload time: 8-9 PM Bangladesh time\n• Highest engagement: Friday-Sunday\n• Average session: 12 minutes",
                    context="Audience demographic insights"
                )
            ]
        }
    
    def _load_bengali_templates(self) -> Dict[str, List[FewShotExample]]:
        """Load Bengali few-shot examples organized by category."""
        return {
            'ctr_analysis': [
                FewShotExample(
                    question="কোন ভিডিওগুলোর CTR সবচেয়ে কম?",
                    answer="আপনার সবচেয়ে কম CTR এর ভিডিওগুলো:\n১. 'রান্নার টিউটোরিয়াল পার্ট ৩' (০.৮%) - ৪৫হাজার ইমপ্রেশন\n২. 'দৈনন্দিন ভ্লগ #১২৭' (১.২%) - ৩২হাজার ইমপ্রেশন\n৩. 'টেক রিভিউ: বাজেট ফোন' (১.৪%) - ২৮হাজার ইমপ্রেশন\n\nএগুলো আপনার গড় ৩.২% CTR থেকে কম পারফর্ম করেছে। উজ্জ্বল রঙ এবং স্পষ্ট টেক্সট দিয়ে থাম্বনেইল আপডেট করার কথা ভাবুন।",
                    context="কম CTR থাম্বনেইল/টাইটেল সমস্যা নির্দেশ করে"
                ),
                FewShotExample(
                    question="গত সপ্তাহে আমার CTR কেন কমেছে?",
                    answer="গত সপ্তাহে আপনার CTR ৪.১% থেকে ২.৮% এ নেমেছে। বিশ্লেষণে দেখা যাচ্ছে:\n\n• ৩টি ভিডিওতে একই ধরনের থাম্বনেইল স্টাইল (লাল ব্যাকগ্রাউন্ড)\n• আপলোড সময় স্বাভাবিক ৮টার বদলে ৬টায় পরিবর্তন\n• আপনার নিশে প্রতিযোগিতা বেড়েছে (৫টি অনুরূপ ভিডিও প্রকাশিত)\n\nসুপারিশ: বিভিন্ন থাম্বনেইল স্টাইল পরীক্ষা করুন এবং ভাল পারফরমেন্সের জন্য ৮টা আপলোডে ফিরে যান।",
                    context="CTR হ্রাসের বহুমুখী বিশ্লেষণ প্রয়োজন"
                )
            ],
            
            'title_optimization': [
                FewShotExample(
                    question="আমার কম পারফরমিং ভিডিওর জন্য ভাল টাইটেল সাজেস্ট করুন",
                    answer="অপ্টিমাইজড টাইটেল সাজেশন:\n\n**বর্তমান:** 'ভাত রান্না'\n**সাজেস্টেড:** 'প্রতিবার পারফেক্ট ভাত - ৩টি গোপন টিপস!' (জরুরি + সুবিধা যোগ করে)\n\n**বর্তমান:** 'ফোন রিভিউ'\n**সাজেস্টেড:** 'এই ২০০ টাকার ফোন আমাকে চমকে দিল - আইফোনের চেয়ে ভাল?' (কৌতূহল + তুলনা)\n\n**বর্তমান:** 'ট্রাভেল ভ্লগ'\n**সাজেস্টেড:** 'বাংলাদেশের লুকানো স্বর্গে ২৪ ঘন্টা কাটালাম' (নির্দিষ্ট + আকর্ষণীয়)\n\nআবেগময় ট্রিগার, সংখ্যা এবং স্পষ্ট সুবিধার উপর ফোকাস করুন।",
                    context="এনগেজমেন্টের জন্য টাইটেল অপ্টিমাইজেশন"
                )
            ],
            
            'performance_trends': [
                FewShotExample(
                    question="আমার ভিডিও পারফরমেন্সে কী ট্রেন্ড দেখছেন?",
                    answer="গত ৩০ দিনের মূল পারফরমেন্স ট্রেন্ড:\n\n📈 **উন্নতি:**\n• গড় দেখার সময়: +১৫% (এখন ২:৩৪ মিনিট)\n• সাবস্ক্রাইবার রূপান্তর: +২২% (৩.৪% দর্শক সাবস্ক্রাইব করে)\n• সপ্তাহান্তের আপলোড ৩০% ভাল পারফর্ম করে\n\n📉 **হ্রাস:**\n• CTR ৮% কমেছে (৪.২% থেকে ৩.৯%)\n• বাংলাদেশ থেকে ভিউ ১২% কমেছে\n\n🎯 **সুযোগ:**\n• খাবারের কন্টেন্ট ২গুণ বেশি এনগেজমেন্ট পায়\n• ৮-১২ মিনিটের ভিডিও সবচেয়ে ভাল পারফর্ম করে\n• বৃহস্পতিবার আপলোডে সর্বোচ্চ রিচ",
                    context="ব্যাপক ট্রেন্ড বিশ্লেষণ"
                )
            ]
        }
    
    def get_system_prompt(self, language: str = 'en', category: str = 'general', 
                         user_question: str = "", data_summary: str = "") -> str:
        """
        Generate a system prompt with few-shot examples.
        
        Args:
            language (str): 'en' or 'bn'
            category (str): Category of examples to include
            user_question (str): The actual user question
            data_summary (str): Summary of the CSV data
            
        Returns:
            str: Complete system prompt with examples
        """
        # Base system prompts
        base_prompts = {
            'en': """You are a YouTube analytics expert and data analyst. Your role is to analyze YouTube channel performance data and provide actionable insights to content creators.

ANALYSIS GUIDELINES:
- Focus on data-driven insights using specific numbers and metrics
- Identify trends, patterns, and correlations in the data
- Provide actionable recommendations for improving channel performance
- Compare performance across different videos and time periods
- Explain what the metrics mean in practical terms for content creators

RESPONSE STYLE:
- Be clear, concise, and professional
- Use bullet points and structured formatting when helpful
- Highlight key findings and most important recommendations
- Explain technical metrics in accessible language
- Focus on practical next steps the creator can take""",
            
            'bn': """আপনি একজন YouTube অ্যানালিটিক্স বিশেষজ্ঞ এবং ডেটা বিশ্লেষক। আপনার ভূমিকা হল YouTube চ্যানেলের পারফরমেন্স ডেটা বিশ্লেষণ করা এবং কন্টেন্ট ক্রিয়েটরদের কার্যকর পরামর্শ প্রদান করা।

বিশ্লেষণের নির্দেশনা:
- নির্দিষ্ট সংখ্যা এবং মেট্রিক্স ব্যবহার করে ডেটা-চালিত অন্তর্দৃষ্টিতে ফোকাস করুন
- ডেটায় ট্রেন্ড, প্যাটার্ন এবং সম্পর্ক চিহ্নিত করুন
- চ্যানেলের পারফরমেন্স উন্নতির জন্য কার্যকর সুপারিশ প্রদান করুন
- বিভিন্ন ভিডিও এবং সময়কালের মধ্যে পারফরমেন্স তুলনা করুন
- কন্টেন্ট ক্রিয়েটরদের জন্য মেট্রিক্সের ব্যবহারিক অর্থ ব্যাখ্যা করুন

উত্তরের ধরন:
- স্পষ্ট, সংক্ষিপ্ত এবং পেশাদার হন
- সহায়ক হলে বুলেট পয়েন্ট এবং কাঠামোগত ফরম্যাটিং ব্যবহার করুন
- মূল ফলাফল এবং সবচেয়ে গুরুত্বপূর্ণ সুপারিশগুলি হাইলাইট করুন
- প্রযুক্তিগত মেট্রিক্স সহজ ভাষায় ব্যাখ্যা করুন
- ক্রিয়েটর যে ব্যবহারিক পদক্ষেপ নিতে পারেন তার উপর ফোকাস করুন"""
        }
        
        # Start with base prompt
        prompt = base_prompts.get(language, base_prompts['en'])
        
        # Add data summary if provided
        if data_summary:
            prompt += f"\n\nDATA OVERVIEW:\n{data_summary}"
        
        # Add few-shot examples if category exists
        if category in self.templates.get(language, {}):
            examples = self.templates[language][category]
            
            prompt += f"\n\nEXAMPLES:\n"
            prompt += "=" * 40 + "\n"
            
            for i, example in enumerate(examples, 1):
                prompt += f"\nExample {i}:\n"
                prompt += f"Q: {example.question}\n"
                prompt += f"A: {example.answer}\n"
                if example.context:
                    prompt += f"Context: {example.context}\n"
                prompt += "-" * 30 + "\n"
        
        # Add the actual user question
        if user_question:
            prompt += f"\nNow answer this question using the same style and depth:\nQ: {user_question}\nA: "
        
        return prompt
    
    def get_category_from_question(self, question: str, language: str = 'en') -> str:
        """
        Determine the most appropriate category based on the user's question.
        
        Args:
            question (str): User's question
            language (str): Language code
            
        Returns:
            str: Category name or 'general' if no match
        """
        question_lower = question.lower()
        
        # English keywords
        if language == 'en':
            if any(keyword in question_lower for keyword in ['ctr', 'click', 'thumbnail', 'drop', 'low']):
                return 'ctr_analysis'
            elif any(keyword in question_lower for keyword in ['title', 'suggest', 'name', 'headline']):
                return 'title_optimization'
            elif any(keyword in question_lower for keyword in ['trend', 'performance', 'growth', 'compare', 'change']):
                return 'performance_trends'
            elif any(keyword in question_lower for keyword in ['audience', 'demographic', 'country', 'viewer']):
                return 'audience_insights'
        
        # Bengali keywords
        elif language == 'bn':
            if any(keyword in question_lower for keyword in ['ctr', 'ক্লিক', 'থাম্বনেইল', 'কম', 'হ্রাস']):
                return 'ctr_analysis'
            elif any(keyword in question_lower for keyword in ['টাইটেল', 'শিরোনাম', 'নাম', 'সাজেস্ট']):
                return 'title_optimization'
            elif any(keyword in question_lower for keyword in ['ট্রেন্ড', 'পারফরমেন্স', 'বৃদ্ধি', 'তুলনা', 'পরিবর্তন']):
                return 'performance_trends'
            elif any(keyword in question_lower for keyword in ['দর্শক', 'অডিয়েন্স', 'দেশ', 'ভিউয়ার']):
                return 'audience_insights'
        
        return 'general'
    
    def get_contextual_prompt(self, user_question: str, language: str = 'en', 
                            data_summary: str = "") -> str:
        """
        Generate a contextual prompt with appropriate few-shot examples.
        
        Args:
            user_question (str): User's question
            language (str): Language code ('en' or 'bn')
            data_summary (str): Summary of the data
            
        Returns:
            str: Complete contextual prompt
        """
        category = self.get_category_from_question(user_question, language)
        return self.get_system_prompt(language, category, user_question, data_summary)

# Global instance for easy import
prompt_manager = PromptTemplateManager()

def get_contextual_prompt(user_question: str, language: str = 'en', data_summary: str = "") -> str:
    """
    Convenience function to get a contextual prompt.
    
    Args:
        user_question (str): User's question
        language (str): Language code
        data_summary (str): Data summary
        
    Returns:
        str: Contextual prompt with examples
    """
    return prompt_manager.get_contextual_prompt(user_question, language, data_summary)

# Example usage and testing
if __name__ == "__main__":
    # Test English prompts
    print("=== ENGLISH CTR ANALYSIS EXAMPLE ===")
    prompt = get_contextual_prompt(
        "Why is my CTR so low?", 
        language='en',
        data_summary="Channel has 50 videos, average CTR 2.1%, total views 500K"
    )
    print(prompt[:500] + "...\n")
    
    # Test Bengali prompts
    print("=== BENGALI TITLE OPTIMIZATION EXAMPLE ===")
    prompt = get_contextual_prompt(
        "আমার ভিডিওর টাইটেল কিভাবে ভাল করব?",
        language='bn',
        data_summary="চ্যানেলে ৫০টি ভিডিও, গড় CTR ২.১%, মোট ভিউ ৫০০হাজার"
    )
    print(prompt[:500] + "...\n")
    
    # Test category detection
    print("=== CATEGORY DETECTION TESTS ===")
    test_questions = [
        ("How can I improve my CTR?", "en"),
        ("Suggest better titles", "en"),
        ("What trends do you see?", "en"),
        ("আমার CTR কেন কম?", "bn"),
        ("ভাল টাইটেল সাজেস্ট করুন", "bn")
    ]
    
    for question, lang in test_questions:
        category = prompt_manager.get_category_from_question(question, lang)
        print(f"'{question}' ({lang}) → {category}")