import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { PublicGroupStandings } from '../types';

/**
 * Formats current date and time in IST (Indian Standard Time).
 */
function getFormattedTimestampIST(): string {
  try {
    const options: Intl.DateTimeFormatOptions = {
      timeZone: 'Asia/Kolkata',
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    };
    return new Intl.DateTimeFormat('en-IN', options).format(new Date()) + ' IST';
  } catch {
    return new Date().toLocaleString() + ' IST';
  }
}

/**
 * Adds page footer with tournament signature and page number.
 */
function applyPageFooters(doc: jsPDF): void {
  const pageCount = doc.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    // Footer top divider
    doc.setDrawColor(220, 220, 220);
    doc.setLineWidth(0.3);
    doc.line(14, 286, 196, 286);

    // Footer text
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(130, 130, 130);
    doc.text('MINARAM CUP 2026 · Official Tournament Standings Document', 14, 291);
    doc.text(`Page ${i} of ${pageCount}`, 196, 291, { align: 'right' });
  }
}

/**
 * Generates and downloads a branded PDF containing ALL group standings.
 */
export function exportAllStandingsPdf(
  groups: PublicGroupStandings[],
  tournamentName = 'MINARAM CUP 2026'
): void {
  if (!groups || groups.length === 0) {
    alert('No standings data available to export.');
    return;
  }

  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const timestamp = getFormattedTimestampIST();

  // Top Red Accent Stripe
  doc.setFillColor(179, 18, 27); // #B3121B
  doc.rect(0, 0, 210, 4.5, 'F');

  // Header Title
  let currentY = 16;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(22);
  doc.setTextColor(18, 18, 18);
  doc.text(tournamentName.toUpperCase(), 14, currentY);

  // Subtitle & Metadata
  currentY += 6;
  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(179, 18, 27);
  doc.text('OFFICIAL EFOOTBALL CHAMPIONSHIP — GROUP STAGE STANDINGS', 14, currentY);

  currentY += 5;
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(90, 90, 90);
  doc.text('TKM College of Engineering · Real-Time Points & Qualification Rankings', 14, currentY);

  doc.setFontSize(8);
  doc.setTextColor(130, 130, 130);
  doc.text(`Generated on: ${timestamp}`, 196, currentY, { align: 'right' });

  // Qualification Rules Banner Box
  currentY += 5;
  doc.setFillColor(246, 247, 249);
  doc.rect(14, currentY, 182, 13, 'F');
  doc.setFillColor(179, 18, 27);
  doc.rect(14, currentY, 2.5, 13, 'F'); // Red left accent border

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.setTextColor(20, 20, 20);
  doc.text('QUALIFICATION PROTOCOL: Top 2 teams from each group advance directly to Round of 16 (RO16) Knockouts.', 19, currentY + 5);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.5);
  doc.setTextColor(100, 100, 100);
  doc.text('Scoring: Win = 3 pts · Draw = 1 pt · Loss = 0 pts | Tie-breakers: Goal Difference (GD) -> Goals For (GF) -> Head-to-Head', 19, currentY + 10);

  currentY += 19;

  // Render Each Group Table
  groups.forEach((group) => {
    const standingsList = group.standings || [];
    // Estimate table height: header (7mm) + each row (6.5mm) + group title (8mm)
    const estimatedHeight = 15 + (standingsList.length + 1) * 6.5;

    // Check if new page is needed
    if (currentY + estimatedHeight > 275) {
      doc.addPage();
      // Thin top red stripe on new pages
      doc.setFillColor(179, 18, 27);
      doc.rect(0, 0, 210, 3, 'F');
      currentY = 16;
    }

    // Group Title Bar
    doc.setFillColor(179, 18, 27);
    doc.rect(14, currentY, 2.5, 5, 'F');

    const cleanGroupName = group.group_name.trim().toLowerCase().startsWith('group')
      ? group.group_name.trim().toUpperCase()
      : `GROUP ${group.group_name.trim().toUpperCase()}`;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10.5);
    doc.setTextColor(20, 20, 20);
    doc.text(cleanGroupName, 19, currentY + 4);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(120, 120, 120);
    doc.text('TOP 2 ADVANCE TO PLAYOFFS', 196, currentY + 4, { align: 'right' });

    currentY += 6.5;

    // Table rows
    const bodyData = standingsList.map((row, idx) => {
      const gdFormatted = row.goal_difference > 0 ? `+${row.goal_difference}` : `${row.goal_difference}`;
      return [
        row.rank || idx + 1,
        row.team_name || 'TBD',
        row.played,
        row.won,
        row.drawn,
        row.lost,
        row.goals_for,
        row.goals_against,
        gdFormatted,
        row.points,
      ];
    });

    autoTable(doc, {
      startY: currentY,
      margin: { left: 14, right: 14 },
      head: [['POS', 'TEAM / SQUAD', 'MP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'PTS']],
      body: bodyData,
      theme: 'grid',
      styles: {
        fontSize: 8,
        cellPadding: 1.8,
        lineColor: [225, 229, 235],
        lineWidth: 0.2,
        textColor: [40, 40, 40],
      },
      headStyles: {
        fillColor: [20, 20, 20],
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 7.5,
        halign: 'center',
      },
      columnStyles: {
        0: { halign: 'center', cellWidth: 12 }, // POS
        1: { halign: 'left', cellWidth: 70, fontStyle: 'bold' }, // TEAM
        2: { halign: 'center', cellWidth: 12 }, // MP
        3: { halign: 'center', cellWidth: 12 }, // W
        4: { halign: 'center', cellWidth: 12 }, // D
        5: { halign: 'center', cellWidth: 12 }, // L
        6: { halign: 'center', cellWidth: 13 }, // GF
        7: { halign: 'center', cellWidth: 13 }, // GA
        8: { halign: 'center', cellWidth: 14 }, // GD
        9: { halign: 'center', cellWidth: 14, fontStyle: 'bold' }, // PTS
      },
      didParseCell: (data) => {
        // Highlight top 2 qualified teams with subtle emerald green background
        if (data.section === 'body') {
          if (data.row.index < 2) {
            data.cell.styles.fillColor = [240, 253, 244]; // Light emerald
            if (data.column.index === 0) {
              data.cell.styles.textColor = [5, 150, 105]; // Emerald-600 rank
              data.cell.styles.fontStyle = 'bold';
            }
          }
          if (data.column.index === 9) {
            data.cell.styles.textColor = [15, 23, 42]; // Slate-900 PTS
          }
        }
      },
    });

    const lastTable = (doc as any).lastAutoTable;
    currentY = (lastTable ? lastTable.finalY : currentY + 30) + 7;
  });

  // Apply page numbers and footers across all generated pages
  applyPageFooters(doc);

  // Trigger download
  doc.save('MinaramCup_Group_Standings_Official.pdf');
}

/**
 * Generates and downloads a branded PDF containing a SINGLE group's standings.
 */
export function exportSingleGroupPdf(
  group: PublicGroupStandings,
  tournamentName = 'MINARAM CUP 2026'
): void {
  if (!group) return;

  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const timestamp = getFormattedTimestampIST();
  const cleanGroupName = group.group_name.trim().toLowerCase().startsWith('group')
    ? group.group_name.trim().toUpperCase()
    : `GROUP ${group.group_name.trim().toUpperCase()}`;

  // Top Red Accent Stripe
  doc.setFillColor(179, 18, 27);
  doc.rect(0, 0, 210, 4.5, 'F');

  // Header
  let currentY = 16;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(22);
  doc.setTextColor(18, 18, 18);
  doc.text(tournamentName.toUpperCase(), 14, currentY);

  currentY += 6;
  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(179, 18, 27);
  doc.text(`OFFICIAL EFOOTBALL CHAMPIONSHIP — ${cleanGroupName} STANDINGS`, 14, currentY);

  currentY += 5;
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(90, 90, 90);
  doc.text('TKM College of Engineering · Group Stage Points Table', 14, currentY);

  doc.setFontSize(8);
  doc.setTextColor(130, 130, 130);
  doc.text(`Generated on: ${timestamp}`, 196, currentY, { align: 'right' });

  // Rules Box
  currentY += 6;
  doc.setFillColor(246, 247, 249);
  doc.rect(14, currentY, 182, 13, 'F');
  doc.setFillColor(179, 18, 27);
  doc.rect(14, currentY, 2.5, 13, 'F');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.setTextColor(20, 20, 20);
  doc.text(`QUALIFICATION PROTOCOL: Top 2 teams from ${cleanGroupName} qualify directly for Knockouts.`, 19, currentY + 5);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.5);
  doc.setTextColor(100, 100, 100);
  doc.text('Scoring: Win = 3 pts · Draw = 1 pt · Loss = 0 pts | Tie-breakers: GD -> Goals For (GF) -> Head-to-Head', 19, currentY + 10);

  currentY += 20;

  // Table
  const standingsList = group.standings || [];
  const bodyData = standingsList.map((row, idx) => {
    const gdFormatted = row.goal_difference > 0 ? `+${row.goal_difference}` : `${row.goal_difference}`;
    return [
      row.rank || idx + 1,
      row.team_name || 'TBD',
      row.played,
      row.won,
      row.drawn,
      row.lost,
      row.goals_for,
      row.goals_against,
      gdFormatted,
      row.points,
    ];
  });

  autoTable(doc, {
    startY: currentY,
    margin: { left: 14, right: 14 },
    head: [['POS', 'TEAM / SQUAD', 'MP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'PTS']],
    body: bodyData,
    theme: 'grid',
    styles: {
      fontSize: 9,
      cellPadding: 2.8,
      lineColor: [225, 229, 235],
      lineWidth: 0.2,
      textColor: [40, 40, 40],
    },
    headStyles: {
      fillColor: [20, 20, 20],
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      fontSize: 8.5,
      halign: 'center',
    },
    columnStyles: {
      0: { halign: 'center', cellWidth: 14 },
      1: { halign: 'left', cellWidth: 68, fontStyle: 'bold' },
      2: { halign: 'center', cellWidth: 12 },
      3: { halign: 'center', cellWidth: 12 },
      4: { halign: 'center', cellWidth: 12 },
      5: { halign: 'center', cellWidth: 12 },
      6: { halign: 'center', cellWidth: 13 },
      7: { halign: 'center', cellWidth: 13 },
      8: { halign: 'center', cellWidth: 14 },
      9: { halign: 'center', cellWidth: 14, fontStyle: 'bold' },
    },
    didParseCell: (data) => {
      if (data.section === 'body') {
        if (data.row.index < 2) {
          data.cell.styles.fillColor = [240, 253, 244];
          if (data.column.index === 0) {
            data.cell.styles.textColor = [5, 150, 105];
            data.cell.styles.fontStyle = 'bold';
          }
        }
        if (data.column.index === 9) {
          data.cell.styles.textColor = [15, 23, 42];
        }
      }
    },
  });

  applyPageFooters(doc);

  const safeGroupSlug = group.group_name.replace(/[^a-zA-Z0-9_-]/g, '_');
  doc.save(`MinaramCup_Group_${safeGroupSlug}_Standings.pdf`);
}
