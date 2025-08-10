import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string

def generate_sample_dataset(num_rows=100000, filename="sample_data.csv"):
    """
    Genera un dataset de muestra para pruebas con datos realistas
    """
    print(f"Generando dataset con {num_rows:,} registros...")
    
    # Configurar semilla para reproducibilidad
    np.random.seed(42)
    random.seed(42)
    
    # Generar datos
    data = {
        'id': range(1, num_rows + 1),
        'timestamp': generate_timestamps(num_rows),
        'user_id': np.random.randint(1000, 9999, num_rows),
        'category': np.random.choice(['Electronics', 'Clothing', 'Books', 'Sports', 'Home'], num_rows),
        'product_name': generate_product_names(num_rows),
        'price': np.round(np.random.exponential(50, num_rows) + 10, 2),
        'quantity': np.random.poisson(2, num_rows) + 1,
        'discount': np.random.choice([0, 5, 10, 15, 20, 25], num_rows, p=[0.4, 0.2, 0.15, 0.15, 0.08, 0.02]),
        'region': np.random.choice(['North', 'South', 'East', 'West', 'Central'], num_rows),
        'customer_age': np.random.normal(35, 12, num_rows).astype(int).clip(18, 80),
        'payment_method': np.random.choice(['Credit Card', 'Debit Card', 'PayPal', 'Cash'], num_rows),
        'rating': np.random.choice([1, 2, 3, 4, 5], num_rows, p=[0.05, 0.1, 0.15, 0.35, 0.35]),
        'is_premium': np.random.choice([True, False], num_rows, p=[0.3, 0.7]),
        'session_duration': np.random.exponential(15, num_rows).round(1),
        'pages_visited': np.random.poisson(5, num_rows) + 1
    }
    
    # Calcular campos derivados
    data['total_amount'] = np.round(
        data['price'] * data['quantity'] * (1 - data['discount'] / 100), 2
    )
    
    # Agregar algunos valores nulos de forma realística
    null_indices = np.random.choice(num_rows, size=int(num_rows * 0.02), replace=False)
    data['rating'] = np.array(data['rating'], dtype=float)
    data['rating'][null_indices] = np.nan
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    # Guardar archivo
    df.to_csv(filename, index=False)
    print(f"Dataset guardado como '{filename}'")
    
    # Mostrar estadísticas
    print(f"\nEstadísticas del dataset:")
    print(f"Filas: {len(df):,}")
    print(f"Columnas: {len(df.columns)}")
    print(f"Tamaño archivo: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    print(f"Valores únicos por columna:")
    for col in df.columns:
        unique_count = df[col].nunique()
        print(f"  {col}: {unique_count:,}")
    
    return df

def generate_timestamps(num_rows):
    """Generar timestamps realistas"""
    start_date = datetime.now() - timedelta(days=365)
    timestamps = []
    
    for _ in range(num_rows):
        # Generar fecha aleatoria en el último año
        random_days = np.random.randint(0, 365)
        random_hours = np.random.randint(0, 24)
        random_minutes = np.random.randint(0, 60)
        
        timestamp = start_date + timedelta(
            days=random_days,
            hours=random_hours,
            minutes=random_minutes
        )
        timestamps.append(timestamp.strftime('%Y-%m-%d %H:%M:%S'))
    
    return timestamps

def generate_product_names(num_rows):
    """Generar nombres de productos realistas"""
    categories = {
        'Electronics': ['iPhone', 'Samsung Galaxy', 'MacBook', 'iPad', 'Sony TV', 'Nintendo Switch'],
        'Clothing': ['T-Shirt', 'Jeans', 'Dress', 'Jacket', 'Sneakers', 'Hat'],
        'Books': ['Fiction Novel', 'Cookbook', 'Biography', 'Science Book', 'History Book', 'Art Book'],
        'Sports': ['Football', 'Basketball', 'Tennis Racket', 'Yoga Mat', 'Dumbbells', 'Running Shoes'],
        'Home': ['Coffee Maker', 'Vacuum Cleaner', 'Lamp', 'Cushion', 'Plant Pot', 'Mirror']
    }
    
    products = []
    for category_items in categories.values():
        products.extend(category_items)
    
    return np.random.choice(products, num_rows)

def generate_large_dataset(num_rows=2000000):
    """Generar dataset grande para pruebas de rendimiento"""
    print(f"Generando dataset GRANDE con {num_rows:,} registros...")
    print("Esto puede tomar varios minutos...")
    
    # Generar en chunks para evitar problemas de memoria
    chunk_size = 100000
    chunks = []
    
    for i in range(0, num_rows, chunk_size):
        current_chunk_size = min(chunk_size, num_rows - i)
        print(f"Procesando chunk {i//chunk_size + 1}/{(num_rows-1)//chunk_size + 1}")
        
        chunk_df = generate_sample_dataset(current_chunk_size, filename=None)
        chunk_df['id'] = range(i + 1, i + current_chunk_size + 1)  # IDs únicos
        chunks.append(chunk_df)
    
    # Combinar chunks
    print("Combinando chunks...")
    final_df = pd.concat(chunks, ignore_index=True)
    
    # Guardar
    filename = f"large_dataset_{num_rows//1000}k.csv"
    print(f"Guardando archivo final: {filename}")
    final_df.to_csv(filename, index=False)
    
    print(f"Dataset grande completado: {len(final_df):,} registros")
    return final_df

# Consultas de ejemplo para el dataset generado
EXAMPLE_QUERIES = {
    'ventas_por_categoria': """
        SELECT 
            category,
            COUNT(*) as total_sales,
            SUM(total_amount) as revenue,
            AVG(total_amount) as avg_order_value
        FROM data 
        GROUP BY category 
        ORDER BY revenue DESC
    """,
    
    'tendencias_temporales': """
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as daily_orders,
            SUM(total_amount) as daily_revenue
        FROM data 
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        LIMIT 30
    """,
    
    'analisis_clientes': """
        SELECT 
            customer_age,
            is_premium,
            COUNT(*) as customer_count,
            AVG(total_amount) as avg_spending
        FROM data 
        GROUP BY customer_age, is_premium
        ORDER BY customer_age
    """,
    
    'productos_top': """
        SELECT 
            product_name,
            category,
            COUNT(*) as sales_count,
            SUM(total_amount) as total_revenue,
            AVG(rating) as avg_rating
        FROM data 
        GROUP BY product_name, category
        HAVING COUNT(*) > 10
        ORDER BY total_revenue DESC
        LIMIT 20
    """,
    
    'analisis_descuentos': """
        SELECT 
            discount,
            COUNT(*) as order_count,
            AVG(total_amount) as avg_order_value,
            SUM(total_amount) as total_revenue
        FROM data 
        GROUP BY discount
        ORDER BY discount
    """,
    
    'regiones_performance': """
        SELECT 
            region,
            COUNT(*) as total_orders,
            SUM(total_amount) as revenue,
            AVG(session_duration) as avg_session_time,
            AVG(pages_visited) as avg_pages
        FROM data 
        GROUP BY region
        ORDER BY revenue DESC
    """,
    
    'cohort_analysis': """
        SELECT 
            DATE_TRUNC('month', timestamp) as month,
            is_premium,
            COUNT(DISTINCT user_id) as unique_customers,
            SUM(total_amount) as monthly_revenue
        FROM data 
        GROUP BY DATE_TRUNC('month', timestamp), is_premium
        ORDER BY month DESC, is_premium DESC
    """
}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generador de datos de prueba')
    parser.add_argument('--rows', type=int, default=100000, 
                       help='Número de filas a generar (default: 100000)')
    parser.add_argument('--large', action='store_true', 
                       help='Generar dataset grande (2M registros)')
    parser.add_argument('--filename', type=str, default='sample_data.csv',
                       help='Nombre del archivo de salida')
    
    args = parser.parse_args()
    
    if args.large:
        generate_large_dataset(2000000)
    else:
        generate_sample_dataset(args.rows, args.filename)
    
    print("\n" + "="*50)
    print("CONSULTAS DE EJEMPLO PARA PROBAR:")
    print("="*50)
    for name, query in EXAMPLE_QUERIES.items():
        print(f"\n-- {name.upper().replace('_', ' ')}:")
        print(query.strip())