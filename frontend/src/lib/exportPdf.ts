import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { apiGet } from "@/lib/api";
import type { Project, Scene, Shot } from "@/types";

export async function generateProjectPdf(project: Project, scenes: Scene[]) {
  const doc = new jsPDF();
  const title = `Project: ${project.title}`;
  
  // Title
  doc.setFontSize(20);
  doc.text(title, 14, 22);
  
  // Metadata
  doc.setFontSize(11);
  doc.setTextColor(100);
  doc.text(`Genre: ${project.genre} | Status: ${project.status}`, 14, 30);
  if (project.description) {
    doc.text(project.description, 14, 38, { maxWidth: 180 });
  }

  let currentY = project.description ? 50 : 40;

  for (const scene of scenes) {
    // Scene Header
    if (currentY > 260) {
      doc.addPage();
      currentY = 20;
    }

    doc.setFontSize(14);
    doc.setTextColor(0);
    const sceneTitle = `Scene ${scene.scene_number}: ${scene.title}`;
    doc.text(sceneTitle, 14, currentY);
    
    doc.setFontSize(10);
    doc.setTextColor(100);
    const sceneMeta = `${scene.location_type.toUpperCase()} - ${scene.time_of_day.toUpperCase()}`;
    doc.text(sceneMeta, 14, currentY + 6);
    currentY += 12;

    // Fetch shots for this scene
    try {
      const shots = await apiGet<Shot[]>(`/api/v1/scenes/${scene.id}/shots`);
      
      if (shots.length === 0) {
        doc.setFontSize(10);
        doc.setTextColor(150);
        doc.text("No shots planned.", 14, currentY);
        currentY += 10;
        continue;
      }

      const tableData = shots.map((shot) => [
        `#${shot.shot_number}`,
        shot.shot_type.replace("_", " "),
        shot.camera_angle.replace("_", " "),
        shot.camera_movement.replace("_", " "),
        shot.lens_mm ? `${shot.lens_mm}mm` : "-",
        shot.description ?? "",
      ]);

      autoTable(doc, {
        startY: currentY,
        head: [["Shot", "Type", "Angle", "Movement", "Lens", "Description"]],
        body: tableData,
        theme: "grid",
        headStyles: { fillColor: [41, 128, 185] },
        margin: { left: 14 },
      });

      // @ts-ignore - autotable adds previousAutoTable to doc
      currentY = doc.previousAutoTable.finalY + 15;
    } catch (err) {
      console.error(`Failed to load shots for scene ${scene.id}`, err);
    }
  }

  // Save the PDF
  doc.save(`${project.title.replace(/\s+/g, "_")}_ShotList.pdf`);
}
