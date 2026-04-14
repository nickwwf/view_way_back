# utf-8 -*-
def iPagenation(pagination):
    total_count = int(pagination.total)
    page_size = int(pagination.per_page)
    page = int(pagination.page)

    total_pages = int(pagination.pages)

    is_prev = 0 if page <= 1 else 1
    is_next = 0 if page >= total_pages else 1
    
    # Convert items to dictionaries explicitly
    items = []
    for item in pagination.items:
        if hasattr(item, 'keys') and hasattr(item, '__getitem__'):
            items.append({key: item[key] for key in item.keys()})
        else:
            items.append({col.name: getattr(item, col.name) for col in item.__table__.columns})
    
    pages = {
        'current': page,
        'total_pages': total_pages,
        'total': total_count,
        'page_size': page_size,
        'is_next': is_next,
        'is_prev': is_prev,
        'items': items
    }

    return pages
