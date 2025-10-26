###################################################################################################
###################################################################################################

import os
import argparse

import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

###################################################################################################
###################################################################################################

def parse_opt():
    parser = argparse.ArgumentParser()

    parser.add_argument('--gt_path', type=str, default='../KISAgt')
    parser.add_argument('--results_path', type=str, default='../KISAresult')
    parser.add_argument('--save_score_path', type=str, default='../KISAtestscore')

    opt = parser.parse_args()
    return opt

###################################################################################################

def parse_time(t):
    return datetime.strptime(t, "%H:%M:%S")

def time_within(start, end, delta_seconds):
    return start >= end - timedelta(seconds=2) and start <= end + timedelta(seconds=delta_seconds)

def evaluate_performance_to_csv_and_txt(gt_folder, pred_folder, save_folder):
    classes = ["PeopleCounting", "Queueing", "Intrusion", "Loitering"]
    overall_metrics = {cls: {"TP": 0, "FP": 0, "GT": 0, "Pred": 0} for cls in classes}
    file_metrics = {}

    # Load all GT files
    for gt_file in [f for f in os.listdir(gt_folder) if f.endswith('.xml')]:
        gt_tree = ET.parse(os.path.join(gt_folder, gt_file))
        gt_root = gt_tree.getroot()
        
        file_results = {}
        
        # For each clip in GT
        for gt_clip in gt_root.findall(".//Clip"):
            gt_filename = gt_clip.find(".//Header/Filename").text
            gt_alarms = gt_clip.findall(".//Alarms/Alarm")
            
            # Load corresponding pred file
            pred_file_path = os.path.join(pred_folder, gt_filename.replace('.mp4', '.xml'))
            if os.path.exists(pred_file_path):
                pred_tree = ET.parse(pred_file_path)
                pred_root = pred_tree.getroot()
                pred_alarms = pred_root.findall(".//Alarms/Alarm")
                
                # Initialize file results for this class
                for alarm in gt_alarms:
                    alarm_class = alarm.find("AlarmDescription").text
                    if alarm_class not in file_results:
                        file_results[alarm_class] = {"TP": 0, "FP": 0, "GT": 0, "Pred": len(pred_alarms)}
                        overall_metrics[alarm_class]["Pred"] += len(pred_alarms)
                
                # Compare alarms
                for gt_alarm in gt_alarms:
                    gt_time = parse_time(gt_alarm.find("StartTime").text)
                    gt_class = gt_alarm.find("AlarmDescription").text
                    overall_metrics[gt_class]["GT"] += 1
                    file_results[gt_class]["GT"] += 1
                    
                    for pred_alarm in pred_alarms:
                        pred_time = parse_time(pred_alarm.find("StartTime").text)
                        pred_class = pred_alarm.find("AlarmDescription").text
                        
                        if gt_class == pred_class:
                            time_diff = 2 if gt_class in ["PeopleCounting", "Queueing"] else 10
                            if time_within(pred_time, gt_time, time_diff):
                                overall_metrics[gt_class]["TP"] += 1
                                file_results[gt_class]["TP"] += 1
                                pred_alarms.remove(pred_alarm)  # Prevent double counting
                                break
                
                # Count false positives
                for pred_alarm in pred_alarms:
                    pred_class = pred_alarm.find("AlarmDescription").text
                    overall_metrics[pred_class]["FP"] += 1
                    if pred_class in file_results:
                        file_results[pred_class]["FP"] += 1
        
        file_metrics[gt_file] = file_results
    
    # Save results to a CSV file and TXT file
    with open(os.path.join(save_folder, 'evaluation_results.csv'), 'w', newline='', encoding='utf-8') as csvfile, open(os.path.join(save_folder, "evaluation_results.txt"), "w", encoding="utf-8") as txtfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Class", "File", "GT Count", "Pred Count", "Recall", "Precision", "F1 Score"])
        txtfile.write("Evaluation Results\n")
        
        for cls in classes:
            metrics = overall_metrics[cls]
            recall = metrics["TP"] / metrics["GT"] if metrics["GT"] > 0 else 0
            precision = metrics["TP"] / (metrics["TP"] + metrics["FP"]) if (metrics["TP"] + metrics["FP"]) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            writer.writerow([cls, "Overall", metrics["GT"], metrics["Pred"], recall, precision, f1_score])
            txtfile.write(f"{cls} Overall Results - GT: {metrics['GT']}, Pred: {metrics['Pred']}, Recall: {recall:.2f}, Precision: {precision:.2f}, F1: {f1_score:.2f}\n")
            
            for filename, results in file_metrics.items():
                if cls in results:
                    r = results[cls]
                    recall = r["TP"] / r["GT"] if r["GT"] > 0 else 0
                    precision = r["TP"] / (r["TP"] + r["FP"]) if (r["TP"] + r["FP"]) > 0 else 0
                    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                    writer.writerow([cls, filename, r["GT"], r["Pred"], recall, precision, f1])
                    txtfile.write(f"{filename} - {cls} - GT: {r['GT']}, Pred: {r['Pred']}, Recall: {recall:.2f}, Precision: {precision:.2f}, F1: {f1:.2f}\n")
            txtfile.write("\n")

###################################################################################################
###################################################################################################

if __name__ == "__main__":
    opt = parse_opt()
    
    # Define paths
    gt_folder = opt.gt_path
    pred_folder = opt.results_path
    save_folder = opt.save_score_path
    
    evaluate_performance_to_csv_and_txt(gt_folder, pred_folder, save_folder)

###################################################################################################
###################################################################################################

