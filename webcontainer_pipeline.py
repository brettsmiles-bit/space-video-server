@@ .. @@
         status = "✅ COMPLETED" if step.get('success', True) else "❌ FAILED"
-        print(f"[{step['timestamp']}] {step_name}: {status}")
+        print(f"[{step['timestamp']}] {step_name}: {status}")
         
         if step.get('details'):
             for key, value in step['details'].items():