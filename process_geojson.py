#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UrbanRay3D - GeoJSON to CSV processor for MATLAB ray-tracing simulation
This script extracts building coordinates and heights from OpenStreetMap GeoJSON
and exports them to a CSV file suitable for MATLAB signal coverage modeling.
"""

import json
import csv
import os
import numpy as np
import matplotlib.pyplot as plt

# Try to import 3D plotting support, but continue if not available
HAS_3D_SUPPORT = False
try:
    from mpl_toolkits.mplot3d import Axes3D
    HAS_3D_SUPPORT = True
except ImportError:
    print("Warning: 3D visualization libraries not available. Will generate CSV only.")

def get_building_height(properties):
    """
    Calculate building height based on properties:
    1. Use 'height' if available
    2. Use 'building:levels' * 3 if available
    3. Default to 3 meters if neither is available
    """
    # Check for direct height property
    if 'height' in properties:
        try:
            return float(properties['height'])
        except (ValueError, TypeError):
            pass
            
    # Check for building levels
    if 'building:levels' in properties:
        try:
            levels = float(properties['building:levels'])
            return levels * 3.0  # Each level is approximately 3 meters
        except (ValueError, TypeError):
            pass
            
    # Default height
    return 3.0

def process_coordinates(coords, height):
    """
    Extract points from a polygon coordinates array
    Only process the exterior ring (first ring) for each polygon
    """
    results = []
    
    # Handle MultiPolygon vs Polygon
    if len(coords) > 0 and isinstance(coords[0][0], list) and not isinstance(coords[0][0][0], list):
        # This is a simple Polygon's coordinates
        exterior_ring = coords[0]  # First ring is exterior
        for point in exterior_ring:
            # Check if point is valid (has at least 2 coordinates)
            if len(point) >= 2:
                lon, lat = point[0], point[1]
                results.append((lon, lat, height))
    else:
        # This is likely a MultiPolygon or a complex Polygon with holes
        for polygon in coords:
            if polygon and len(polygon) > 0:
                exterior_ring = polygon[0]  # First ring is exterior
                for point in exterior_ring:
                    # Check if point is valid (has at least 2 coordinates)
                    if len(point) >= 2:
                        lon, lat = point[0], point[1]
                        results.append((lon, lat, height))
                        
    return results

def process_geojson(file_path, output_csv_path, output_img_path=None):
    """
    Process GeoJSON file and extract building data
    """
    building_points = []
    
    # Read and parse the GeoJSON file
    with open(file_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    # Process each feature in the GeoJSON
    for feature in geojson_data.get('features', []):
        geometry = feature.get('geometry', {})
        properties = feature.get('properties', {})
        
        # Only process features with polygon geometries
        if geometry and geometry.get('type') in ['Polygon', 'MultiPolygon']:
            # Calculate building height
            height = get_building_height(properties)
            
            # Extract coordinates based on geometry type
            if geometry.get('type') == 'Polygon':
                building_points.extend(process_coordinates(geometry.get('coordinates', []), height))
            elif geometry.get('type') == 'MultiPolygon':
                for polygon_coords in geometry.get('coordinates', []):
                    building_points.extend(process_coordinates([polygon_coords], height))
    
    # Write to CSV file
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write header
        csv_writer.writerow(['longitude', 'latitude', 'height_meters'])
        # Write data
        csv_writer.writerows(building_points)
    
    # Create 2D visualization if 3D is not available
    if building_points and output_img_path:
        if HAS_3D_SUPPORT:
            try:
                create_3d_visualization(building_points, output_img_path)
            except Exception as e:
                print(f"Could not create 3D visualization: {str(e)}")
                create_2d_visualization(building_points, output_img_path)
        else:
            create_2d_visualization(building_points, output_img_path)
        
    return len(building_points)

def create_2d_visualization(points, output_path):
    """
    Create a 2D visualization of the buildings with height represented by color
    """
    # Extract coordinates
    x, y, z = zip(*points)
    
    plt.figure(figsize=(10, 8))
    
    # Plot the buildings as a scatter plot
    scatter = plt.scatter(x, y, c=z, cmap='viridis', alpha=0.5, s=2)
    
    # Add color bar
    cbar = plt.colorbar(scatter, label='Height (meters)')
    
    # Set labels
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Building Data for Urban Ray Tracing (Height shown by color)')
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_3d_visualization(points, output_path):
    """
    Create a 3D scatter plot visualization of the buildings
    """
    if not HAS_3D_SUPPORT:
        print("3D visualization not available.")
        return
        
    # Extract coordinates
    x, y, z = zip(*points)
    
    # Create the 3D plot
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot the buildings
    scatter = ax.scatter(x, y, z, c=z, cmap='viridis', alpha=0.5, s=2)
    
    # Add color bar
    cbar = plt.colorbar(scatter, ax=ax, label='Height (meters)')
    
    # Set labels
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_zlabel('Height (meters)')
    ax.set_title('3D Building Data for Urban Ray Tracing')
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    # File paths
    input_geojson = "/home/halil/Desktop/repos/UrbanRay3D/export.geojson"
    output_csv = "/home/halil/Desktop/repos/UrbanRay3D/output/buildings.csv"
    output_img = "/home/halil/Desktop/repos/UrbanRay3D/output/preview.png"
    
    # Process the data
    num_points = process_geojson(input_geojson, output_csv, output_img)
    print(f"Processed {num_points} building points. Results saved to {output_csv}")
    if os.path.exists(output_img):
        print(f"Visualization saved to {output_img}")