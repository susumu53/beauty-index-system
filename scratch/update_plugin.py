import os
import re

file_path = "beauty-index-generator.php"

# Attempt to read the file with different encodings
content = None
for enc in ["utf-8", "cp932", "shift-jis", "euc-jp"]:
    try:
        with open(file_path, "r", encoding=enc) as f:
            content = f.read()
        print(f"Successfully read with {enc}")
        break
    except Exception:
        continue

if not content:
    print("Could not read file with any encoding.")
    exit(1)

# Check if route already exists
if "delete-entry" in content:
    print("Route already exists.")
else:
    # Add route
    route_pattern = r"register_rest_route\('beauty-index/v1', '/update-score', \["
    replacement = """register_rest_route('beauty-index/v1', '/update-score', [
            'methods' => 'POST',
            'callback' => [$this, 'handle_rest_score_update'],
            'permission_callback' => '__return_true', // 本番はトークン認証推奨
        ]);

        register_rest_route('beauty-index/v1', '/delete-entry', [
            'methods' => 'POST',
            'callback' => [$this, 'handle_rest_delete_entry'],
            'permission_callback' => '__return_true',
        ]);"""
    
    # We need to replace the entire block or use a safer regex
    # Let's find the handle_rest_score_update function and insert after it or add the new handler
    
    # Add handle_rest_delete_entry method
    method_insertion = """
    public function handle_rest_delete_entry($request) {
        $params = $request->get_json_params();
        $name = sanitize_text_field($params['name']);
        $year = isset($params['year']) ? intval($params['year']) : intval(date('Y'));

        if (empty($name)) return new WP_Error('invalid_data', 'Name is required', ['status' => 400]);

        $this->delete_ranking_entry($year, $name);

        return rest_ensure_response(['success' => true, 'message' => 'Entry deleted: ' . $name]);
    }
"""

    # Insert route
    content = content.replace("register_rest_route('beauty-index/v1', '/update-score', [", replacement.split('\n')[0])
    # The above replace is too simple and might break. Let's use a more precise replacement for the whole block.
    
    # Let's use string manipulation to insert the method before the next public function
    content = content.replace("update_option('beauty_index_annual_ranking', $ranking);", "update_option('beauty_index_annual_ranking', $ranking);\n    }\n" + method_insertion)
    
    # Fix the routes
    content = re.sub(
        r"register_rest_route\('beauty-index/v1', '/update-score', \[.*?\]\s*\);",
        replacement.strip(),
        content,
        flags=re.DOTALL
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("File updated successfully.")
