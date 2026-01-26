"""
Report generation and export functionality.
"""

import json
import csv
import logging
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate and export evaluation reports in multiple formats."""
    
    def __init__(self, output_dir: str = "./reports"):
        """Initialize report generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_csv(self, results: List[Dict], filename: str = "evaluation_results.csv") -> str:
        """
        Export results to CSV format.
        
        Args:
            results: List of evaluation results
            filename: Output filename
        
        Returns:
            Path to generated file
        """
        filepath = self.output_dir / filename
        
        if not results:
            logger.warning("No results to export")
            return ""
        
        # Flatten results for CSV
        flattened = []
        for result in results:
            flat_result = {
                "student": result.get("student"),
                "repository": result.get("repository"),
                "final_score": result.get("final_score"),
                "letter_grade": result.get("letter_grade"),
                "feedback": result.get("feedback", "")
            }
            
            # Add metric breakdowns
            for metric_name, metric_data in result.get("metrics", {}).items():
                flat_result[f"{metric_name}_score"] = metric_data.get("score")
                flat_result[f"{metric_name}_weight"] = metric_data.get("weight")
            
            flattened.append(flat_result)
        
        # Get all possible fieldnames
        fieldnames = ["student", "repository", "final_score", "letter_grade"]
        if flattened:
            fieldnames.extend([k for k in flattened[0].keys() if k not in fieldnames])
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened)
            
            logger.info(f"CSV report saved to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error writing CSV: {e}")
            return ""
    
    def export_json(self, results: List[Dict], filename: str = "evaluation_results.json") -> str:
        """
        Export results to JSON format.
        
        Args:
            results: List of evaluation results
            filename: Output filename
        
        Returns:
            Path to generated file
        """
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"JSON report saved to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error writing JSON: {e}")
            return ""
    
    def export_text(self, results: List[Dict], filename: str = "evaluation_report.txt") -> str:
        """
        Export results to human-readable text format.
        
        Args:
            results: List of evaluation results
            filename: Output filename
        
        Returns:
            Path to generated file
        """
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("GITHUB CLASSROOM EVALUATION REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                # Summary statistics
                if results:
                    scores = [r.get("final_score", 0) for r in results]
                    f.write("SUMMARY STATISTICS\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Total Students Evaluated: {len(results)}\n")
                    if scores:
                        f.write(f"Average Score: {sum(scores)/len(scores):.2f}\n")
                        f.write(f"Highest Score: {max(scores):.2f}\n")
                        f.write(f"Lowest Score: {min(scores):.2f}\n")
                    else:
                        f.write("No scores to report\n")
                    f.write(f"\nGrade Distribution:\n")
                    
                    grades = {}
                    for r in results:
                        grade = r.get("letter_grade", "N/A")
                        grades[grade] = grades.get(grade, 0) + 1
                    
                    for grade in sorted(grades.keys(), reverse=True):
                        count = grades[grade]
                        percentage = (count / len(results)) * 100
                        f.write(f"  {grade}: {count} students ({percentage:.1f}%)\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("INDIVIDUAL STUDENT RESULTS\n")
                f.write("=" * 80 + "\n\n")
                
                # Individual results
                for result in sorted(results, key=lambda x: x.get("final_score", 0), reverse=True):
                    f.write(f"Student: {result.get('student')}\n")
                    f.write(f"Repository: {result.get('repository')}\n")
                    f.write(f"Final Score: {result.get('final_score'):.2f}/100\n")
                    f.write(f"Grade: {result.get('letter_grade')}\n")
                    f.write(f"Feedback: {result.get('feedback', 'N/A')}\n")
                    f.write("\nMetric Breakdown:\n")
                    
                    for metric_name, metric_data in result.get("metrics", {}).items():
                        f.write(f"  {metric_name}:\n")
                        f.write(f"    Score: {metric_data.get('score'):.2f}/100\n")
                        f.write(f"    Weight: {metric_data.get('weight')}%\n")
                        f.write(f"    Details: {metric_data.get('details')}\n")
                    
                    f.write("-" * 40 + "\n\n")
            
            logger.info(f"Text report saved to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error writing text report: {e}")
            return ""
    
    def export_all_formats(self, results: List[Dict]) -> List[str]:
        """
        Export results in all configured formats.
        
        Args:
            results: List of evaluation results
        
        Returns:
            List of file paths created
        """
        files = []
        files.append(self.export_csv(results))
        files.append(self.export_json(results))
        files.append(self.export_text(results))
        
        return [f for f in files if f]
