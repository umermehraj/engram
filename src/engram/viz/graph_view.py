"""Interactive knowledge graph visualization using pyvis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyvis.network import Network

# Color palette for entity types
ENTITY_COLORS = {
    # Abstract entities
    "person": "#4CAF50",       # green
    "project": "#2196F3",      # blue
    "tool": "#FF9800",         # orange
    "concept": "#9C27B0",      # purple
    "preference": "#E91E63",   # pink
    "organization": "#00BCD4", # cyan
    # Data source nodes
    "document": "#FFD54F",     # amber
    "conversation": "#81C784", # light green
    "image": "#CE93D8",        # light purple
    "video": "#EF5350",        # red
    "audio": "#42A5F5",        # light blue
    "file": "#A1887F",         # brown
    "webpage": "#26C6DA",      # teal
    "code": "#66BB6A",         # green
    "default": "#757575",      # gray
}

# Node shapes by category
ENTITY_SHAPES = {
    # Abstract entities → circles
    "person": "dot", "project": "dot", "tool": "dot",
    "concept": "diamond", "preference": "star", "organization": "dot",
    # Data sources → distinct shapes
    "document": "square", "conversation": "triangle",
    "image": "square", "video": "triangleDown",
    "audio": "diamond", "file": "square",
    "webpage": "triangle", "code": "square",
    "default": "dot",
}

# Edge colors by relationship type signal strength
EDGE_COLORS = {
    # High-signal: bold
    "decided": "#F44336",      # red
    "prefers": "#E91E63",      # pink
    "believes": "#9C27B0",     # purple
    "works_on": "#2196F3",     # blue
    "replaced": "#FF5722",     # deep orange
    # Medium-signal: muted
    "mentioned": "#BDBDBD",    # light gray
    "asked_about": "#BDBDBD",
    "related_to": "#90CAF9",   # light blue
    "depends_on": "#FFB74D",   # light orange
    "part_of": "#81C784",      # light green
    # Meta: dashed style handled separately
    "contradicts": "#F44336",
    "supersedes": "#FF9800",
    "derived_from": "#78909C",
}

EDGE_WIDTHS = {
    "decided": 3, "prefers": 3, "believes": 2.5, "works_on": 2.5, "replaced": 3,
    "mentioned": 1, "asked_about": 1, "related_to": 1.5,
    "depends_on": 2, "part_of": 2,
    "contradicts": 2, "supersedes": 2, "derived_from": 1.5,
}


def build_graph_html(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    title: str = "Engram Knowledge Graph",
    height: str = "800px",
    width: str = "100%",
    output_path: str | None = None,
) -> str:
    """
    Build an interactive HTML graph visualization.

    Args:
        entities: List of entity dicts with keys: id, name, entity_type, summary, confidence
        relationships: List of relationship dicts with keys: from_entity_id, to_entity_id,
                      rel_type, summary, confidence, valid_from, invalid_from
        title: Page title
        height: CSS height
        width: CSS width
        output_path: If set, write HTML to this file path

    Returns:
        HTML string of the interactive graph
    """
    net = Network(
        height=height,
        width=width,
        directed=True,
        bgcolor="#1a1a2e",
        font_color="#e0e0e0",
        heading=title,
    )

    # Physics settings for a nice layout
    net.set_options(json.dumps({
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 200,
                "springConstant": 0.04,
                "damping": 0.09,
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
        },
        "interaction": {
            "hover": True,
            "tooltipDelay": 100,
            "navigationButtons": True,
            "keyboard": True,
        },
        "edges": {
            "smooth": {"type": "continuous"},
        },
    }))

    # Add nodes
    entity_id_set = set()
    for entity in entities:
        eid = entity["id"]
        etype = entity.get("entity_type", "default")
        color = ENTITY_COLORS.get(etype, ENTITY_COLORS["default"])
        confidence = entity.get("confidence", 1.0)
        summary = entity.get("summary", entity.get("name", ""))

        # Data source nodes are larger; abstract entities scale with confidence
        is_source = etype in (
            "document", "conversation", "image", "video", "audio", "file", "webpage", "code"
        )
        size = 30 if is_source else 15 + (confidence * 20)
        shape = ENTITY_SHAPES.get(etype, ENTITY_SHAPES["default"])

        # Richer tooltip for data sources
        source_label = entity.get("metadata", {}).get("source_path", "")
        tooltip = (
            f"<b>{entity['name']}</b><br>"
            f"Type: {etype}<br>"
            f"Confidence: {confidence:.2f}<br>"
            f"Summary: {summary}"
        )
        if source_label:
            tooltip += f"<br>Source: {source_label}"

        net.add_node(
            eid,
            label=entity["name"],
            color=color,
            size=size,
            title=tooltip,
            shape=shape,
            borderWidth=2,
            borderWidthSelected=4,
            font={"size": 14, "face": "Inter, sans-serif"},
        )
        entity_id_set.add(eid)

    # Add edges (only for active relationships)
    for rel in relationships:
        from_id = rel.get("from_entity_id")
        to_id = rel.get("to_entity_id")

        # Skip edges where nodes don't exist
        if from_id not in entity_id_set or to_id not in entity_id_set:
            continue

        # Skip invalidated relationships
        if rel.get("invalid_from") is not None:
            continue

        rel_type = rel.get("rel_type", "related_to")
        if hasattr(rel_type, "value"):
            rel_type = rel_type.value

        color = EDGE_COLORS.get(rel_type, "#757575")
        width = EDGE_WIDTHS.get(rel_type, 1.5)
        summary = rel.get("summary", rel_type)

        # Dashed style for meta edges
        dashes = rel_type in ("contradicts", "supersedes", "derived_from")

        tooltip = (
            f"<b>{rel_type}</b><br>"
            f"{summary}<br>"
            f"Confidence: {rel.get('confidence', 1.0):.2f}"
        )

        net.add_edge(
            from_id,
            to_id,
            label=rel_type,
            color=color,
            width=width,
            title=tooltip,
            arrows="to",
            dashes=dashes,
            font={"size": 10, "color": "#999", "align": "middle"},
        )

    html = net.generate_html()

    # Inject custom CSS for dark theme + legend
    legend_html = _build_legend_html()
    html = html.replace("</body>", f"{legend_html}</body>")

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(html)

    return html


def _build_legend_html() -> str:
    """Build an HTML legend overlay for entity types and edge types."""
    source_types = {"document", "conversation", "image", "video", "audio", "file", "webpage", "code"}

    entity_items = []
    source_items = []
    for etype, color in ENTITY_COLORS.items():
        if etype == "default":
            continue
        shape = ENTITY_SHAPES.get(etype, "dot")
        # Use different markers for shapes
        if shape == "square":
            marker = f'<span style="width:12px;height:12px;background:{color};display:inline-block;border-radius:2px"></span>'
        elif shape in ("diamond", "star"):
            marker = f'<span style="width:12px;height:12px;background:{color};display:inline-block;transform:rotate(45deg);border-radius:2px"></span>'
        elif shape in ("triangle", "triangleDown"):
            marker = f'<span style="width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:12px solid {color};display:inline-block"></span>'
        else:
            marker = f'<span style="width:12px;height:12px;border-radius:50%;background:{color};display:inline-block"></span>'

        item = (
            f'<div style="display:flex;align-items:center;gap:6px;margin:2px 0">'
            f'{marker}<span>{etype}</span></div>'
        )
        if etype in source_types:
            source_items.append(item)
        else:
            entity_items.append(item)

    items = entity_items  # keep backward compat variable for the template below

    return f"""
    <div style="position:fixed;top:10px;right:10px;background:rgba(26,26,46,0.9);
                border:1px solid #444;border-radius:8px;padding:12px 16px;
                color:#e0e0e0;font-family:Inter,sans-serif;font-size:12px;
                z-index:9999;max-width:180px">
        <div style="font-weight:bold;margin-bottom:8px;font-size:13px">Entities</div>
        {''.join(entity_items)}
        <div style="font-weight:bold;margin-top:10px;margin-bottom:6px;font-size:13px">Data Sources</div>
        {''.join(source_items)}
        <div style="font-weight:bold;margin-top:10px;margin-bottom:6px;font-size:13px">Edge Signals</div>
        <div style="display:flex;align-items:center;gap:6px;margin:2px 0">
            <span style="width:20px;height:3px;background:#F44336;display:inline-block"></span>
            <span>high-signal</span>
        </div>
        <div style="display:flex;align-items:center;gap:6px;margin:2px 0">
            <span style="width:20px;height:2px;background:#90CAF9;display:inline-block"></span>
            <span>medium-signal</span>
        </div>
        <div style="display:flex;align-items:center;gap:6px;margin:2px 0">
            <span style="width:20px;height:2px;background:#78909C;display:inline-block;border-top:2px dashed #78909C"></span>
            <span>meta (dashed)</span>
        </div>
    </div>
    """


async def visualize_user_graph(
    graph_backend,
    user_id: str,
    tenant_id: str = "default",
    output_path: str = "engram_graph.html",
    max_entities: int = 200,
) -> str:
    """
    Fetch a user's knowledge graph and render it as interactive HTML.

    Args:
        graph_backend: KuzuBackend instance
        user_id: User whose graph to visualize
        tenant_id: Tenant ID
        output_path: Where to write the HTML file
        max_entities: Max entities to include

    Returns:
        Path to the generated HTML file
    """
    # Fetch entities
    entities_obj = await graph_backend.list_entities(
        user_id=user_id, tenant_id=tenant_id, limit=max_entities
    )
    entities = [e.model_dump() for e in entities_obj]

    # Fetch relationships for each entity
    relationships = []
    seen_rel_ids = set()
    for entity in entities:
        rels = await graph_backend.get_active_relationships(entity["id"])
        for r in rels:
            if r.id not in seen_rel_ids:
                relationships.append(r.model_dump())
                seen_rel_ids.add(r.id)

    build_graph_html(
        entities=entities,
        relationships=relationships,
        title=f"Engram Knowledge Graph — {user_id}",
        output_path=output_path,
    )

    return output_path
