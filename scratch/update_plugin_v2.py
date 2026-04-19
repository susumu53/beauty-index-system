import os
import re

file_path = "beauty-index-generator.php"

try:
    with open(file_path, "rb") as f:
        raw_data = f.read()
    
    # Try different decodings with replacement for errors
    content = raw_data.decode('utf-8', errors='ignore')
    print("Read file with utf-8 (ignoring errors)")
    
    # Check if route already exists
    if "delete-entry" in content:
        print("Route already exists.")
    else:
        # Route registration
        route_pattern = r"register_rest_route\s*\(\s*'beauty-index/v1'\s*,\s*'/update-score'\s*,.*?\);"
        new_routes = """register_rest_route('beauty-index/v1', '/update-score', [
            'methods' => 'POST',
            'callback' => [$this, 'handle_rest_score_update'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route('beauty-index/v1', '/delete-entry', [
            'methods' => 'POST',
            'callback' => [$this, 'handle_rest_delete_entry'],
            'permission_callback' => '__return_true',
        ]);"""
        
        content = re.sub(route_pattern, new_routes, content, flags=re.DOTALL)

        # Handler method
        handler_code = """
    public function handle_rest_delete_entry($request) {
        $params = $request->get_json_params();
        $name = sanitize_text_field($params['name'] ?? '');
        $year = isset($params['year']) ? intval($params['year']) : intval(date('Y'));

        if (empty($name)) return new WP_Error('invalid_data', 'Name is required', ['status' => 400]);

        $this->delete_ranking_entry($year, $name);

        return rest_ensure_response(['success' => true, 'message' => 'Entry deleted: ' . $name]);
    }
"""
        # Insert before the end of the class
        if "delete_ranking_entry" in content:
            # Insert after the delete_ranking_entry function
            content = content.replace("update_option('beauty_index_annual_ranking', $ranking);\n        }\n    }", "update_option('beauty_index_annual_ranking', $ranking);\n        }\n    }\n" + handler_code)
        else:
            # Fallback insertion
            content = content.rstrip()
            if content.endswith("}"):
                content = content[:-1] + handler_code + "\n}"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("File updated successfully.")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
