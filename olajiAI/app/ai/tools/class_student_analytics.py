from app.ai.tools.base import ToolContext, ToolResult

async def run(ctx: ToolContext, query_type: str = "class_distribution") -> ToolResult:
    """
    Analyze classes and students together
    query_type options:
    - "class_distribution": Classes with student count per class
    - "grade_summary": Students grouped by grade level
    - "empty_classes": Classes with no students
    - "full_report": Complete analytics
    """
    
    # Fetch both classes and students
    classes_resp = await ctx.http.get("/classes", ctx.bearer, ctx.school_id)
    students_resp = await ctx.http.get("/students", ctx.bearer, ctx.school_id)
    
    if classes_resp.status_code != 200 or students_resp.status_code != 200:
        return {
            "status": "error", 
            "body": {
                "detail": f"Failed to fetch data: classes={classes_resp.status_code}, students={students_resp.status_code}"
            }
        }
    
    classes = classes_resp.json() or []
    students = students_resp.json() or []
    
    # Create class lookup and student count mapping
    class_lookup = {cls["id"]: cls for cls in classes}
    student_count_by_class = {}
    
    # Count students per class
    for student in students:
        class_id = student.get("class_id")
        if class_id:
            student_count_by_class[class_id] = student_count_by_class.get(class_id, 0) + 1
    
    # Generate analytics based on query type
    if query_type == "class_distribution":
        class_data = []
        for cls in classes:
            class_id = cls["id"]
            student_count = student_count_by_class.get(class_id, 0)
            class_data.append({
                "class_id": class_id,
                "class_name": cls.get("name", "Unknown"),
                "level": cls.get("level", "Unknown"),
                "academic_year": cls.get("academic_year", "Unknown"),
                "stream": cls.get("stream"),
                "student_count": student_count
            })
        
        return {
            "status": 200,
            "body": {
                "type": "class_distribution",
                "total_classes": len(classes),
                "total_students": len(students),
                "classes": class_data
            }
        }
    
    elif query_type == "grade_summary":
        grade_stats = {}
        for cls in classes:
            level = cls.get("level", "Unknown")
            class_id = cls["id"]
            student_count = student_count_by_class.get(class_id, 0)
            
            if level not in grade_stats:
                grade_stats[level] = {"classes": 0, "students": 0, "class_names": []}
            
            grade_stats[level]["classes"] += 1
            grade_stats[level]["students"] += student_count
            grade_stats[level]["class_names"].append(cls.get("name", "Unknown"))
        
        return {
            "status": 200,
            "body": {
                "type": "grade_summary", 
                "total_grades": len(grade_stats),
                "grades": grade_stats
            }
        }
    
    elif query_type == "empty_classes":
        empty_classes = []
        for cls in classes:
            class_id = cls["id"]
            if student_count_by_class.get(class_id, 0) == 0:
                empty_classes.append({
                    "class_id": class_id,
                    "class_name": cls.get("name", "Unknown"),
                    "level": cls.get("level", "Unknown")
                })
        
        return {
            "status": 200,
            "body": {
                "type": "empty_classes",
                "empty_count": len(empty_classes),
                "total_classes": len(classes),
                "empty_classes": empty_classes
            }
        }
    
    else:  # full_report
        # Combine all analytics
        class_data = []
        grade_stats = {}
        empty_classes = []
        
        for cls in classes:
            class_id = cls["id"]
            student_count = student_count_by_class.get(class_id, 0)
            level = cls.get("level", "Unknown")
            
            # Class distribution data
            class_info = {
                "class_id": class_id,
                "class_name": cls.get("name", "Unknown"),
                "level": level,
                "student_count": student_count
            }
            class_data.append(class_info)
            
            # Grade summary data
            if level not in grade_stats:
                grade_stats[level] = {"classes": 0, "students": 0}
            grade_stats[level]["classes"] += 1
            grade_stats[level]["students"] += student_count
            
            # Empty classes
            if student_count == 0:
                empty_classes.append(class_info)
        
        return {
            "status": 200,
            "body": {
                "type": "full_report",
                "summary": {
                    "total_classes": len(classes),
                    "total_students": len(students),
                    "empty_classes": len(empty_classes),
                    "grades_offered": len(grade_stats)
                },
                "class_distribution": class_data,
                "grade_summary": grade_stats,
                "empty_classes": empty_classes
            }
        }