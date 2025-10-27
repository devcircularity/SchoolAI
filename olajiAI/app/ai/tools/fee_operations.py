from app.ai.tools.base import ToolContext, ToolResult
from typing import Dict, Any, List

async def view_fee_structure(ctx: ToolContext, level: str = None, term: int = None, year: int = None) -> ToolResult:
    """View CBC fee structure - with overview support and comprehensive error handling"""
    
    try:
        # Set defaults if not specified
        if not year:
            year = 2025  # Current year
        if not term:
            term = 1    # Default to Term 1
        
        # If no level specified, show comprehensive overview across all levels
        if not level:
            return await _show_fee_overview(ctx, term, year)
        
        # Build specific query for the structure
        params = [f"level={level}", f"term={term}", f"year={year}"]
        url = f"/fees/structures?{'&'.join(params)}"
        
        # Debug logging
        print(f"🔍 Requesting fee structure: {url}")
        
        # Use your CoreHTTP signature: get(path, bearer, school_id)
        r = await ctx.http.get(url, ctx.bearer, ctx.school_id)
        
        print(f"🔍 Response status: {r.status_code}")
        print(f"🔍 Response content: {r.content if hasattr(r, 'content') else 'No content attr'}")
        
        if r.status_code != 200:
            error_detail = "Failed to fetch fee structure"
            try:
                if r.content:
                    error_body = r.json()
                    error_detail = error_body.get("detail", error_detail)
            except Exception:
                pass
            
            return {
                "status": r.status_code, 
                "body": {
                    "detail": error_detail,
                    "suggestion": "Check if the fee structure exists for this level and term."
                }
            }
        
        try:
            structures = r.json() or []
        except Exception as json_error:
            print(f"🔍 Failed to parse JSON response: {json_error}")
            return {
                "status": 500,
                "body": {
                    "detail": "Invalid response format from fee structure API",
                    "error": str(json_error)
                }
            }
        
        print(f"🔍 Found {len(structures)} structures")
        
        if not structures:
            return {
                "status": 404, 
                "body": {
                    "detail": f"No fee structure found for {level}, Term {term}, {year}",
                    "suggestion": "You may need to create classes first, or the fee structure may not be set up for this level."
                }
            }
        
        # Get the matching structure
        structure = structures[0]
        print(f"🔍 Using structure: {structure.get('name')} for level {structure.get('level')}")
        
        # Verify we got the right level
        if structure.get("level") != level:
            print(f"⚠️ WARNING: Requested {level} but got {structure.get('level')}")
            return {
                "status": 404,
                "body": {
                    "detail": f"Fee structure mismatch: requested {level} but found {structure.get('level')}",
                    "available_levels": [s.get("level") for s in structures]
                }
            }
        
        # Get fee items for this structure
        try:
            items_r = await ctx.http.get(f"/fees/structures/{structure['id']}/items", ctx.bearer, ctx.school_id)
            
            if items_r.status_code == 200:
                structure["items"] = items_r.json() or []
            else:
                print(f"🔍 Warning: Could not fetch items for structure {structure['id']}: {items_r.status_code}")
                structure["items"] = []
        except Exception as items_error:
            print(f"🔍 Error fetching items: {items_error}")
            structure["items"] = []
        
        # Format the structure for display
        formatted = format_cbc_structure(structure)
        
        return {
            "status": 200,
            "body": {
                "structure": structure,
                "formatted": formatted,
                "level": level,
                "term": term,
                "year": year
            }
        }
    
    except Exception as e:
        print(f"🔍 ERROR in view_fee_structure: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": 500,
            "body": {
                "detail": f"Internal error while viewing fee structure: {str(e)}",
                "error_type": type(e).__name__
            }
        }

async def set_fee_prices(ctx: ToolContext, price_pairs: List[Dict[str, Any]], 
                        default_level: str = None, term: int = None, year: int = None) -> ToolResult:
    """Set prices for fee items - FIXED VERSION with comprehensive error handling"""
    
    try:
        print(f"🔍 DEBUG set_fee_prices called with:")
        print(f"   price_pairs: {price_pairs}")
        print(f"   default_level: {default_level}")
        print(f"   term: {term}")
        print(f"   year: {year}")
        
        # Validate input
        if not price_pairs:
            return {
                "status": 400,
                "body": {
                    "detail": "No price pairs provided",
                    "suggestion": "Please specify fee prices like 'Set Grade 1 Term 1 fees at 10000'"
                }
            }
        
        # Set defaults
        if not year:
            year = 2025
        if not term:
            term = 1
        
        # Handle different price pair formats
        processed_pairs = []
        for pair in price_pairs:
            # Extract level from pair or use default
            target_level = pair.get("level") or default_level
            target_term = pair.get("term") or term
            target_year = pair.get("year") or year
            
            print(f"🔍 Processing pair: {pair} -> level={target_level}, term={target_term}, year={target_year}")
            
            if not target_level:
                return {
                    "status": 400,
                    "body": {
                        "detail": "No level specified. Please specify which class level to update (e.g., 'Grade 1', 'PP1')",
                        "example": "Set Grade 1 Tuition at 150000"
                    }
                }
            
            # Find the appropriate fee structure for this level/term/year
            structure_r = await _find_fee_structure(ctx, target_level, target_term, target_year)
            if structure_r["status"] != 200:
                print(f"🔍 Could not find fee structure for {target_level} Term {target_term} {target_year}")
                return structure_r
            
            structure = structure_r["body"]
            structure_id = structure["id"]
            
            print(f"🔍 Found structure {structure_id} for {target_level}")
            
            # Prepare the item update
            item_update = {
                "item_name": pair["item_name"],
                "amount": float(pair["amount"])
            }
            
            print(f"🔍 Will update item: {item_update}")
            
            # Handle special case where "fees" means "Tuition"
            if item_update["item_name"].lower() in ["fees", "fee"]:
                item_update["item_name"] = "Tuition"
            
            # Update the fee structure immediately
            payload = {"items": [item_update]}
            
            print(f"🔍 Sending PATCH to /fees/structures/{structure_id}/items with payload: {payload}")
            
            r = await ctx.http.patch(
                f"/fees/structures/{structure_id}/items",
                ctx.bearer,
                ctx.school_id, 
                payload,
                ctx.message_id
            )
            
            print(f"🔍 PATCH response: status={r.status_code}")
            if hasattr(r, 'content') and r.content:
                try:
                    response_body = r.json()
                    print(f"🔍 PATCH response body: {response_body}")
                except Exception as json_error:
                    print(f"🔍 Could not parse PATCH response as JSON: {json_error}")
                    print(f"🔍 Raw response content: {r.content}")
            
            if r.status_code not in [200, 201]:
                error_detail = "Failed to update fee structure"
                try:
                    if r.content:
                        error_body = r.json()
                        error_detail = error_body.get("detail", error_detail)
                except Exception:
                    pass
                
                return {
                    "status": r.status_code,
                    "body": {"detail": f"Failed to update {item_update['item_name']}: {error_detail}"}
                }
            
            processed_pairs.append({
                "level": target_level,
                "item_name": item_update["item_name"],
                "amount": item_update["amount"],
                "structure_id": structure_id
            })
        
        # Return success with all updates
        return {
            "status": 200,
            "body": {
                "updated_items": processed_pairs,
                "message": f"Successfully updated {len(processed_pairs)} fee item(s)"
            }
        }
    
    except Exception as e:
        print(f"🔍 ERROR in set_fee_prices: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": 500,
            "body": {
                "detail": f"Internal error while setting fee prices: {str(e)}",
                "error_type": type(e).__name__
            }
        }

async def _find_fee_structure(ctx: ToolContext, level: str, term: int = None, year: int = None) -> ToolResult:
    """Helper to find the best matching fee structure - ENHANCED"""
    
    # Set defaults
    if not year:
        year = 2025
    if not term:
        term = 1
    
    # Try exact match first
    params = [f"level={level}", f"term={term}", f"year={year}"]
    url = f"/fees/structures?{'&'.join(params)}"
    
    print(f"🔍 Looking for fee structure: {url}")
    
    r = await ctx.http.get(url, ctx.bearer, ctx.school_id)
    
    if r.status_code == 200:
        structures = r.json() or []
        if structures:
            print(f"🔍 Found exact match: {structures[0].get('id')} for {level}")
            return {"status": 200, "body": structures[0]}
    
    # If no exact match, try to find any structure for this level
    r = await ctx.http.get(f"/fees/structures?level={level}", ctx.bearer, ctx.school_id)
    
    if r.status_code == 200:
        structures = r.json() or []
        if structures:
            # Pick the most recent one
            best_match = max(structures, key=lambda s: (s.get("year", 0), s.get("term", 0)))
            print(f"🔍 Found fallback match: {best_match.get('id')} for {level}")
            return {"status": 200, "body": best_match}
    
    # If still no match, try to get all structures and find similar levels
    r = await ctx.http.get("/fees/structures", ctx.bearer, ctx.school_id)
    
    if r.status_code == 200:
        all_structures = r.json() or []
        available_levels = [s.get("level") for s in all_structures]
        
        return {
            "status": 404, 
            "body": {
                "detail": f"No fee structure found for {level}",
                "available_levels": list(set(available_levels)),
                "suggestion": f"Try creating a class for {level} first, or use one of the available levels."
            }
        }
    
    return {
        "status": 404,
        "body": {
            "detail": f"No fee structures found in the system",
            "suggestion": "Create some classes first to generate fee structures"
        }
    }

async def _show_fee_overview(ctx: ToolContext, term: int, year: int) -> ToolResult:
    """Show comprehensive fee overview across all levels"""
    
    # Get all fee structures for the school
    r = await ctx.http.get("/fees/structures", ctx.bearer, ctx.school_id)
    
    if r.status_code != 200:
        return {"status": r.status_code, "body": r.json() if r.content else None}
    
    all_structures = r.json() or []
    
    if not all_structures:
        return {
            "status": 404,
            "body": {
                "detail": "No fee structures found for this school",
                "suggestion": "You may need to create classes and set up fee structures first."
            }
        }
    
    # Group structures by level and calculate totals
    level_data = {}
    
    for structure in all_structures:
        level = structure.get("level")
        struct_term = structure.get("term", 1)
        struct_year = structure.get("year", year)
        
        # Only include structures for the specified year
        if struct_year != year:
            continue
            
        if level not in level_data:
            level_data[level] = {
                "level": level,
                "group": _get_cbc_group(level),
                "term_1": 0,
                "term_2": 0, 
                "term_3": 0,
                "annual": 0,
                "structures": {}
            }
        
        # Get items for this structure
        items_r = await ctx.http.get(f"/fees/structures/{structure['id']}/items", ctx.bearer, ctx.school_id)
        items = items_r.json() if items_r.status_code == 200 else []
        
        # Calculate total for this term
        term_total = sum(item.get("amount", 0) for item in items if item.get("amount") is not None)
        
        # Store structure data
        level_data[level]["structures"][struct_term] = {
            "total": term_total,
            "items": items,
            "structure_id": structure.get("id")
        }
        
        # Update term totals
        if struct_term == 1:
            level_data[level]["term_1"] = term_total
        elif struct_term == 2:
            level_data[level]["term_2"] = term_total
        elif struct_term == 3:
            level_data[level]["term_3"] = term_total
    
    # Calculate annual totals
    for level, data in level_data.items():
        data["annual"] = data["term_1"] + data["term_2"] + data["term_3"]
    
    # Sort levels by CBC progression
    sorted_levels = sorted(level_data.keys(), key=_get_level_sort_order)
    
    # Create table data
    table_rows = []
    for level in sorted_levels:
        data = level_data[level]
        table_rows.append([
            f"{level} ({data['group']})",
            f"{data['term_1']:,.0f} KES" if data['term_1'] > 0 else "Not Set",
            f"{data['term_2']:,.0f} KES" if data['term_2'] > 0 else "Not Set", 
            f"{data['term_3']:,.0f} KES" if data['term_3'] > 0 else "Not Set",
            f"{data['annual']:,.0f} KES" if data['annual'] > 0 else "Not Set"
        ])
    
    # Calculate summary statistics
    total_levels = len(level_data)
    configured_levels = len([d for d in level_data.values() if d['annual'] > 0])
    grand_total_range = [d['annual'] for d in level_data.values() if d['annual'] > 0]
    
    summary_text = f"**Fee Structure Overview for {year}**\n\n"
    summary_text += f"• **{configured_levels} of {total_levels}** levels have configured fees\n"
    
    if grand_total_range:
        min_annual = min(grand_total_range)
        max_annual = max(grand_total_range)
        summary_text += f"• **Annual fees range**: {min_annual:,.0f} - {max_annual:,.0f} KES\n"
    
    unconfigured = [level for level, data in level_data.items() if data['annual'] == 0]
    if unconfigured:
        summary_text += f"• **Needs configuration**: {', '.join(unconfigured[:3])}"
        if len(unconfigured) > 3:
            summary_text += f" and {len(unconfigured) - 3} more"
        summary_text += "\n"
    
    return {
        "status": 200,
        "body": {
            "action": "overview",
            "formatted": {
                "type": "table_with_text",
                "text": summary_text,
                "table": {
                    "type": "table",
                    "title": f"School Fee Structure Overview - {year}",
                    "headers": ["Class", "Term 1", "Term 2", "Term 3", "Total Annual"],
                    "rows": table_rows
                },
                "summary": f"💡 Click on any level above to view detailed fee breakdown."
            },
            "year": year,
            "total_levels": total_levels,
            "configured_levels": configured_levels
        }
    }

def _get_level_sort_order(level: str) -> int:
    """Get sort order for CBC levels"""
    level_order = {
        "PP1": 1, "PP2": 2,
        "Grade 1": 3, "Grade 2": 4, "Grade 3": 5,
        "Grade 4": 6, "Grade 5": 7, "Grade 6": 8,
        "Grade 7": 9, "Grade 8": 10, "Grade 9": 11,
        "Grade 10": 12, "Grade 11": 13, "Grade 12": 14
    }
    return level_order.get(level, 999)

def _get_cbc_group(level: str) -> str:
    """Get CBC group name for a level"""
    cbc_groups = {
        "Early Years Education (EYE)": ["PP1", "PP2"],
        "Lower Primary": ["Grade 1", "Grade 2", "Grade 3"],
        "Upper Primary": ["Grade 4", "Grade 5", "Grade 6"], 
        "Junior Secondary (JSS)": ["Grade 7", "Grade 8", "Grade 9"],
        "Senior Secondary": ["Grade 10", "Grade 11", "Grade 12"],
    }
    
    for group, levels in cbc_groups.items():
        if level in levels:
            return group
    return "Unknown"

async def publish_fee_structure(ctx: ToolContext, level: str = None, term: int = None, year: int = None) -> ToolResult:
    """Publish a fee structure to lock it for invoice generation"""
    # Find the structure to publish
    structure_r = await _find_fee_structure(ctx, level, term, year)
    if structure_r["status"] != 200:
        return structure_r
    
    fee_structure_id = structure_r["body"]["id"]
    
    # Use your CoreHTTP signature: post(path, bearer, school_id, data, idem_key)
    r = await ctx.http.post(
        f"/fees/structures/{fee_structure_id}/publish",
        ctx.bearer,
        ctx.school_id,
        {},  # Empty payload
        ctx.message_id
    )
    
    return {
        "status": r.status_code,
        "body": r.json() if r.content else None
    }

async def generate_invoices(ctx: ToolContext, level: str = None, term: int = None, year: int = None) -> ToolResult:
    """Generate invoices for students"""
    payload = {}
    
    if level:
        payload["level"] = level
    if term:
        payload["term"] = term  
    if year:
        payload["year"] = year
    
    # Use your CoreHTTP signature: post(path, bearer, school_id, data, idem_key)
    r = await ctx.http.post(
        "/invoices/generate",
        ctx.bearer,
        ctx.school_id,
        payload,
        ctx.message_id
    )
    
    return {
        "status": r.status_code,
        "body": r.json() if r.content else None
    }

def format_cbc_structure(structure):
    """Format CBC fee structure for chat display with table support"""
    items = structure.get("items", [])
    level = structure.get("level", "Unknown")
    term = structure.get("term", 1)
    year = structure.get("year", 2025)
    
    # Group by category and billing cycle
    tuition_items = [item for item in items if item.get("item_name") == "Tuition"]
    cocurricular_items = [item for item in items if item.get("item_name") in [
        "Ballet / Dance", "Taekwondo", "Chess", "Roller Skating", "Swimming (KG/Clubs)",
        "Monkeynastix", "French (KG/Clubs)", "Mandarin", "Little Einsteins Club", 
        "Tennis", "Football Academy (Sat)", "Robotics", "Coding", "School Trip (Local)"
    ]]
    other_items = [item for item in items if item not in tuition_items and item not in cocurricular_items]
    
    # Check if we should return table format
    if len(items) > 5:  # Use table for many items
        return {
            "type": "table_with_text",
            "text": f"**{level} — Term {term}, {year}**",
            "table": {
                "type": "table",
                "title": "Fee Structure Breakdown",
                "headers": ["Fee Item", "Category", "Type", "Amount", "Status"],
                "rows": [
                    [
                        item.get("item_name", "Unknown"),
                        _get_item_category(item.get("item_name", "")),
                        "Optional" if item.get("is_optional") else "Required",
                        f"{item.get('amount'):,.0f} KES" if item.get('amount') is not None else "Not Set",
                        "✅ Priced" if item.get('amount') is not None else "⚠️ Needs Pricing"
                    ]
                    for item in items
                ]
            },
            "summary": _get_pricing_summary(items)
        }
    
    # Fallback to text format for fewer items
    output = []
    output.append(f"**{level} — Term {term}, {year}**\n")
    
    # Required termly fees (Tuition)
    if tuition_items:
        output.append("**Required Termly Fees**")
        for item in tuition_items:
            name = item.get("item_name", "Unknown")
            amount = item.get("amount")
            if amount is not None:
                output.append(f"• **{name}**: {amount:,.0f} KES")
            else:
                output.append(f"• **{name}**: *Not priced*")
        output.append("")
    
    # Co-curricular activities (optional, per term)
    if cocurricular_items:
        output.append("**Co-curricular Activities (Per Term)**")
        for item in cocurricular_items:
            name = item.get("item_name", "Unknown")
            amount = item.get("amount")
            if amount is not None:
                output.append(f"• {name}: {amount:,.0f} KES")
            else:
                output.append(f"• {name}: *Not priced*")
        output.append("")
    
    # Other charges
    if other_items:
        output.append("**Other Charges**")
        for item in other_items:
            name = item.get("item_name", "Unknown")
            amount = item.get("amount")
            optional = " (Optional)" if item.get("is_optional") else ""
            if amount is not None:
                output.append(f"• {name}: {amount:,.0f} KES{optional}")
            else:
                output.append(f"• {name}: *Not priced*{optional}")
    
    # Show unpriced items summary
    unpriced = [item for item in items if item.get("amount") is None]
    if unpriced:
        output.append(f"\n**⚠️ {len(unpriced)} items need pricing**")
        for item in unpriced[:3]:
            output.append(f"• {item.get('item_name')}")
        if len(unpriced) > 3:
            output.append(f"• ... and {len(unpriced) - 3} more")
    
    return "\n".join(output)

def _get_item_category(item_name: str) -> str:
    """Get category for fee item"""
    if item_name == "Tuition":
        return "Tuition"
    elif item_name in ["Ballet / Dance", "Taekwondo", "Chess", "Roller Skating", "Swimming (KG/Clubs)",
                      "Monkeynastix", "French (KG/Clubs)", "Mandarin", "Little Einsteins Club", 
                      "Tennis", "Football Academy (Sat)", "Robotics", "Coding", "School Trip (Local)"]:
        return "Co-curricular"
    elif item_name in ["Application", "Registration", "Caution"]:
        return "Admission"
    elif item_name in ["Annual Student Accident Insurance Cover", "Workbooks"]:
        return "Annual"
    elif item_name in ["Sports T-Shirt", "Polo T-Shirts"]:
        return "Uniform"
    else:
        return "Other"

def _get_pricing_summary(items: list) -> str:
    """Get pricing summary for fee structure"""
    total_items = len(items)
    priced_items = len([item for item in items if item.get("amount") is not None])
    unpriced_items = total_items - priced_items
    
    if unpriced_items == 0:
        return f"✅ All {total_items} items are priced and ready for invoicing"
    else:
        return f"⚠️ {unpriced_items} of {total_items} items need pricing before publishing"