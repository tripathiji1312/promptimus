import requests
import json
import os
import time
import re
import html

# --- 1. ENHANCED CONFIGURATION ---

TOPICS = {
    "git": {"site": "stackoverflow", "limit": 60},  # Increased limits
    "bash": {"site": "unix.stackexchange.com", "limit": 45},
    "grep": {"site": "unix.stackexchange.com", "limit": 30},
    "find": {"site": "unix.stackexchange.com", "limit": 30},
    "tar": {"site": "stackoverflow", "limit": 25},
    "ssh": {"site": "unix.stackexchange.com", "limit": 25},
    "venv": {"site": "stackoverflow", "limit": 20},
    "chmod": {"site": "unix.stackexchange.com", "limit": 15},
    # Added more topics to reach 150+
    "awk": {"site": "unix.stackexchange.com", "limit": 20},
    "sed": {"site": "unix.stackexchange.com", "limit": 20},
    "python": {"site": "stackoverflow", "limit": 30},
    "docker": {"site": "stackoverflow", "limit": 25},
}

OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "qa_data.json")


# --- 2. CLEANING FUNCTION ---

def clean_response(body):
    """
    Cleans the body of a Stack Exchange answer.
    """
    if not body:
        return ""

    # Unescape HTML entities
    text = html.unescape(body)

    # Convert code blocks (4+ spaces indentation to markdown)
    lines = text.split('\n')
    cleaned_lines = []
    in_code_block = False

    for line in lines:
        # Check if line is code (starts with 4+ spaces and isn't empty)
        if re.match(r'^    \S', line):
            if not in_code_block:
                cleaned_lines.append('```bash')
                in_code_block = True
            cleaned_lines.append(line[4:])  # Remove the 4 spaces
        else:
            if in_code_block:
                cleaned_lines.append('```')
                in_code_block = False
            # Remove HTML tags but preserve some formatting
            line = re.sub(r'<code>(.*?)</code>', r'`\1`', line)
            line = re.sub(r'<pre><code>(.*?)</code></pre>', r'```\n\1\n```', line, flags=re.DOTALL)
            line = re.sub(r'<[^>]+>', '', line)
            cleaned_lines.append(line)

    if in_code_block:
        cleaned_lines.append('```')

    text = '\n'.join(cleaned_lines)
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# --- 3. MULTI-PAGE COLLECTION ---

def fetch_questions_multiple_pages(site, tags, limit):
    """Fetch questions across multiple pages to get more results."""
    print(f"Fetching questions for '{','.join(tags)}' from {site}...")

    all_qa_pairs = []
    page = 1
    max_pages = 3  # Fetch up to 3 pages

    try:
        while len(all_qa_pairs) < limit and page <= max_pages:
            print(f"  Page {page}: Getting questions...")

            # Step 1: Get questions with pagination
            questions_url = "https://api.stackexchange.com/2.3/questions"
            questions_params = {
                "site": site,
                "tagged": ";".join(tags),
                "order": "desc",
                "sort": "votes",
                "pagesize": 50,  # Max allowed
                "page": page,
                "filter": "withbody"
            }

            questions_response = requests.get(questions_url, params=questions_params, timeout=30)
            questions_response.raise_for_status()
            questions_data = questions_response.json()

            questions_items = questions_data.get('items', [])
            print(f"  ✓ Got {len(questions_items)} questions on page {page}")

            if not questions_items:
                print(f"  No more questions on page {page}")
                break

            # Filter for questions that have accepted answers
            questions_with_accepted = []
            for q in questions_items:
                if q.get('is_answered', False) and q.get('accepted_answer_id'):
                    questions_with_accepted.append(q)

            print(f"  Found {len(questions_with_accepted)} questions with accepted answers")

            if not questions_with_accepted:
                page += 1
                continue

            # Step 2: Get answers in batches to avoid URL length limits
            batch_size = 15
            for i in range(0, len(questions_with_accepted), batch_size):
                batch = questions_with_accepted[i:i + batch_size]
                question_ids = [str(q['question_id']) for q in batch]

                print(f"  Getting answers for batch {i // batch_size + 1} ({len(question_ids)} questions)...")

                answers_url = f"https://api.stackexchange.com/2.3/questions/{';'.join(question_ids)}/answers"
                answers_params = {
                    "site": site,
                    "order": "desc",
                    "sort": "votes",
                    "pagesize": 100,
                    "filter": "withbody"
                }

                answers_response = requests.get(answers_url, params=answers_params, timeout=30)
                answers_response.raise_for_status()
                answers_data = answers_response.json()

                # Process this batch
                accepted_answers = {}
                for answer in answers_data.get('items', []):
                    if answer.get('is_accepted', False):
                        accepted_answers[answer['question_id']] = answer

                questions_dict = {q['question_id']: q for q in batch}

                for question_id, answer in accepted_answers.items():
                    if question_id in questions_dict:
                        question = questions_dict[question_id]

                        instruction = question.get('title', '').strip()
                        answer_body = answer.get('body', '')

                        if instruction and answer_body and len(instruction) > 10:
                            response_text = clean_response(answer_body)

                            if len(response_text.strip()) > 30:
                                all_qa_pairs.append({
                                    "instruction": html.unescape(instruction),
                                    "response": response_text,
                                    "question_score": question.get('score', 0),
                                    "answer_score": answer.get('score', 0),
                                    "question_id": question_id,
                                    "has_full_answer": True,
                                    "tags": question.get('tags', []),
                                    "topic": tags[0]
                                })

                print(f"  ✓ Processed batch, total so far: {len(all_qa_pairs)}")

                # Short delay between batches
                time.sleep(0.5)

            page += 1

            # Check if we have enough
            if len(all_qa_pairs) >= limit:
                print(f"  ✓ Reached target of {limit} questions")
                break

            # Delay between pages
            time.sleep(1)

        print(f"  ✓ Total collected for {tags}: {len(all_qa_pairs)} Q&A pairs")
        return all_qa_pairs[:limit]  # Trim to exact limit

    except requests.exceptions.RequestException as e:
        print(f"  ✗ Request failed: {e}")
        return all_qa_pairs
    except Exception as e:
        print(f"  ✗ Processing failed: {e}")
        return all_qa_pairs


# --- 4. ALTERNATIVE SORTING METHODS ---

def fetch_questions_by_activity(site, tags, limit):
    """Alternative approach using activity-based sorting."""
    print(f"  Alternative: Fetching by recent activity for {tags}...")

    try:
        questions_url = "https://api.stackexchange.com/2.3/questions"
        questions_params = {
            "site": site,
            "tagged": ";".join(tags),
            "order": "desc",
            "sort": "activity",  # Different sorting
            "pagesize": min(limit, 40),
            "filter": "withbody"
        }

        questions_response = requests.get(questions_url, params=questions_params, timeout=30)
        questions_response.raise_for_status()
        questions_data = questions_response.json()

        questions_with_accepted = []
        for q in questions_data.get('items', []):
            if q.get('is_answered', False) and q.get('accepted_answer_id'):
                questions_with_accepted.append(q)

        if not questions_with_accepted:
            return []

        # Get answers
        question_ids = [str(q['question_id']) for q in questions_with_accepted[:20]]

        answers_url = f"https://api.stackexchange.com/2.3/questions/{';'.join(question_ids)}/answers"
        answers_params = {
            "site": site,
            "order": "desc",
            "sort": "votes",
            "pagesize": 100,
            "filter": "withbody"
        }

        answers_response = requests.get(answers_url, params=answers_params, timeout=30)
        answers_response.raise_for_status()
        answers_data = answers_response.json()

        # Process
        accepted_answers = {}
        for answer in answers_data.get('items', []):
            if answer.get('is_accepted', False):
                accepted_answers[answer['question_id']] = answer

        qa_pairs = []
        questions_dict = {q['question_id']: q for q in questions_with_accepted}

        for question_id, answer in accepted_answers.items():
            if question_id in questions_dict:
                question = questions_dict[question_id]

                instruction = question.get('title', '').strip()
                answer_body = answer.get('body', '')

                if instruction and answer_body and len(instruction) > 10:
                    response_text = clean_response(answer_body)

                    if len(response_text.strip()) > 30:
                        qa_pairs.append({
                            "instruction": html.unescape(instruction),
                            "response": response_text,
                            "question_score": question.get('score', 0),
                            "answer_score": answer.get('score', 0),
                            "question_id": question_id,
                            "has_full_answer": True,
                            "tags": question.get('tags', []),
                            "topic": tags[0],
                            "method": "activity_based"
                        })

        print(f"  Alternative method found {len(qa_pairs)} additional pairs")
        return qa_pairs

    except Exception as e:
        print(f"  Alternative method failed: {e}")
        return []


# --- 5. MAIN EXECUTION ---

if __name__ == "__main__":
    print("Stack Exchange Q&A Collector (Enhanced Version)")
    print("=" * 50)
    print(f"Target: 250+ Q&A pairs")

    all_qa_pairs = []
    collected_ids = set()  # Track to avoid duplicates

    for topic, config in TOPICS.items():
        print(f"\n--- Processing topic: {topic.upper()} (target: {config['limit']}) ---")

        # Method 1: Multi-page collection
        pairs = fetch_questions_multiple_pages(config["site"], [topic], config["limit"])

        # Add unique pairs
        for pair in pairs:
            if pair['question_id'] not in collected_ids:
                all_qa_pairs.append(pair)
                collected_ids.add(pair['question_id'])

        current_count = len([p for p in all_qa_pairs if p.get('topic') == topic])
        print(f"✓ Method 1 collected {current_count} pairs for '{topic}'")

        # Method 2: Try alternative sorting if we need more
        if current_count < config["limit"] * 0.7:  # If we got less than 70% of target
            print(f"  Need more for {topic}, trying alternative method...")
            alt_pairs = fetch_questions_by_activity(config["site"], [topic], config["limit"] // 2)

            # Add unique pairs
            added = 0
            for pair in alt_pairs:
                if pair['question_id'] not in collected_ids:
                    all_qa_pairs.append(pair)
                    collected_ids.add(pair['question_id'])
                    added += 1

            print(f"  Alternative method added {added} more pairs")

        final_count = len([p for p in all_qa_pairs if p.get('topic') == topic])
        print(f"✓ Total for '{topic}': {final_count} pairs")

        # Show a sample if we got data
        topic_pairs = [p for p in all_qa_pairs if p.get('topic') == topic]
        if topic_pairs:
            sample = topic_pairs[0]
            print(f"  Sample: {sample['instruction'][:60]}...")
            print(f"  Answer preview: {sample['response'][:80]}...")

        # Delay between topics
        time.sleep(2)

        # Progress update
        print(f"  Running total: {len(all_qa_pairs)} Q&A pairs")

    print(f"\n{'=' * 50}")
    print(f"FINAL SUMMARY: Collected {len(all_qa_pairs)} total Q&A pairs")

    # Show breakdown by topic
    print(f"\n--- BREAKDOWN BY TOPIC ---")
    for topic in TOPICS.keys():
        topic_count = len([p for p in all_qa_pairs if p.get('topic') == topic])
        print(f"  {topic}: {topic_count} pairs")

    # Save the data
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_qa_pairs, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved data to: {OUTPUT_FILE}")

    # Show statistics
    if all_qa_pairs:
        full_answers = sum(1 for pair in all_qa_pairs if pair.get('has_full_answer', False))
        print(f"✓ {full_answers} pairs have full answers")

        # Show score statistics
        scores = [pair['question_score'] for pair in all_qa_pairs]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        print(f"✓ Score stats - Avg: {avg_score:.1f}, Max: {max_score}, Min: {min_score}")

        print(f"\n--- SAMPLE DATA ---")
        for i, pair in enumerate(all_qa_pairs[:3]):
            print(f"\nSample {i + 1} ({pair.get('topic', 'unknown')}):")
            print(f"Q: {pair['instruction']}")
            print(f"A: {pair['response'][:150]}..." if len(pair['response']) > 150 else f"A: {pair['response']}")
            print(f"Scores: Q={pair['question_score']}, A={pair['answer_score']}")

    else:
        print("✗ No data was collected.")

    print(f"\n🎯 TARGET ACHIEVED: {len(all_qa_pairs)} >= 150" if len(
        all_qa_pairs) >= 150 else f"❌ TARGET MISSED: {len(all_qa_pairs)} < 150")
    print(f"✓ Complete! Review the data in '{OUTPUT_FILE}'")