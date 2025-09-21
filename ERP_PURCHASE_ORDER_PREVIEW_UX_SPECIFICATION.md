# Purchase Order Preview Modal - UX Design Specification

## Executive Summary
This specification redesigns the Purchase Order Preview Modal with focus on A4 print optimization, enhanced user experience, and professional document presentation. The redesign addresses critical issues with table width truncation, page overflow, currency display inefficiency, and overall preview UX.

## Current State Analysis

### Identified Problems
1. **Print Layout Issues**
   - Table content gets truncated with many columns (7.5pt font insufficient)
   - A4 page height causes content overflow to invisible second pages
   - Fixed column widths don't optimize for available print space
   - Page boundary visualization is unclear

2. **Currency Display Problems**
   - "NT$ " prefix takes excessive space in narrow columns
   - Inconsistent formatting between screen and print modes
   - Currency alignment issues in print preview

3. **UX Deficiencies**
   - Print preview mode doesn't clearly show page boundaries
   - Modal dialog doesn't scale properly for different screen sizes
   - Limited responsive design for mobile/tablet viewing
   - Poor visual hierarchy in preview mode

4. **Technical Issues**
   - CSS print styles are overly complex and conflicting
   - Multiple print stylesheet approaches causing inconsistency
   - Hard-coded measurements don't account for printer margins
   - Font scaling issues between screen and print modes

## Design Principles

### User-Centric Design
- **Clear Visual Hierarchy**: Information organized by importance and reading flow
- **Print-First Approach**: Screen design optimized for eventual print output
- **Progressive Disclosure**: Show essential info first, details on demand
- **Accessibility**: WCAG 2.1 AA compliance for all users

### Professional Document Standards
- **Consistent Typography**: Clear hierarchy with readable font sizes
- **Brand Alignment**: Consistent with TSIC corporate identity
- **Print Optimization**: Designed specifically for A4 (210mm × 297mm)
- **Legal Compliance**: Meets procurement document standards

## Redesigned User Experience

### 1. Modal Layout Structure

#### Primary Modal (Screen View)
```
┌─────────────────────────────────────────────────────────┐
│ 採購單預覽 Purchase Order Preview        [Controls] [×] │
├─────────────────────────────────────────────────────────┤
│ [View Mode Tabs]  [Edit] | [Print Preview] | [Export]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─── Screen Preview Area (Scrollable) ─────────────┐   │
│  │  • Company Header with Logo                     │   │
│  │  • Purchase Order Info Table                    │   │
│  │  • Items Table (Full width, responsive)         │   │
│  │  • Totals Section                               │   │
│  │  • Terms & Conditions                           │   │
│  │  • Signature Area                               │   │
│  │  ─────────── Print Boundary ──────────          │   │
│  │  • Additional Info (Non-printable)              │   │
│  │  • Supplier Details (Extended)                  │   │
│  │  • Delivery Information                         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ [Close] [Print Preview] [Export Excel] [Export PDF]     │
└─────────────────────────────────────────────────────────┘
```

#### Print Preview Mode
```
┌─────────────────────────────────────────────────────────┐
│ 列印預覽模式 Print Preview Mode         [Controls] [×]  │
├─────────────────────────────────────────────────────────┤
│ [返回編輯] [縮放: 75% ▼] [頁面: 1/2 ◄►] [列印設定]       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│    ┌─── A4 Page Preview (210mm × 297mm) ───────┐       │
│    │ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │       │
│    │ ┃  [TSIC Logo]    採購單     [Status]  ┃ │       │
│    │ ┃                                     ┃ │       │
│    │ ┃  ┌─ Supplier Info ─┐ ┌─ PO Info ─┐  ┃ │       │
│    │ ┃  │ 廠商名稱: ABC   │ │ 單號: P001 │  ┃ │       │
│    │ ┃  └────────────────┘ └───────────┘  ┃ │       │
│    │ ┃                                     ┃ │       │
│    │ ┃  採購明細 Purchase Items             ┃ │       │
│    │ ┃  ┌─────────────────────────────────┐ ┃ │       │
│    │ ┃  │ 項│品名    │規格│數量│單價│小計│ ┃ │       │
│    │ ┃  │ 次│        │    │    │    │    │ ┃ │       │
│    │ ┃  └─────────────────────────────────┘ ┃ │       │
│    │ ┃                                     ┃ │       │
│    │ ┃              總計: $123,456         ┃ │       │
│    │ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │       │
│    └─────────────────────────────────────────────┘       │
│    Page 1 of 2 - Print boundaries clearly visible        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ [返回編輯] [列印] [Export PDF] [共享連結]                │
└─────────────────────────────────────────────────────────┘
```

### 2. View Modes

#### Edit Mode (Default)
- **Purpose**: Primary viewing and editing interface
- **Features**: 
  - Editable quotation number field
  - Terms template selector
  - Full supplier information display
  - Status information and export history
  - Responsive table with horizontal scroll if needed

#### Print Preview Mode
- **Purpose**: WYSIWYG preview of final printed document
- **Features**:
  - Exact A4 page dimensions (210mm × 297mm)
  - Clear page boundary visualization
  - Zoom controls (50%, 75%, 100%, 125%, 150%)
  - Multi-page support with navigation
  - Print-optimized typography and spacing

#### Export Mode
- **Purpose**: Streamlined interface during export operations
- **Features**:
  - Read-only interface
  - Progress indicators
  - Export options (Excel, PDF, Print)
  - Status updates

### 3. Responsive Design Strategy

#### Desktop (1200px+)
- Modal width: 1400px (increased from 1200px)
- Print preview: Full A4 scale (100%)
- Table columns: All visible with optimal widths
- Side-by-side layouts for comparison

#### Tablet (768px - 1199px)
- Modal width: 95vw
- Print preview: 75% scale
- Stacked layouts for complex sections
- Touch-optimized controls

#### Mobile (< 768px)
- Full-screen modal
- Print preview: 50% scale with pinch-zoom
- Simplified navigation
- Priority-based information display

## A4 Print Layout Optimization

### Page Specifications
- **Paper Size**: A4 (210mm × 297mm)
- **Margins**: 15mm top, 10mm sides, 20mm bottom
- **Printable Area**: 190mm × 262mm
- **Content Safety Zone**: 170mm × 240mm (accounting for printer variations)

### Typography System

#### Print Font Hierarchy
```
Title (採購單): 20pt, Bold, #000000
Subtitle (PURCHASE ORDER): 14pt, Regular, #333333
Section Headers: 12pt, Bold, #000000
Table Headers: 10pt, SemiBold, #000000
Body Text: 9pt, Regular, #000000
Small Text: 8pt, Regular, #666666
Currency: 9pt, Monospace (for alignment)
```

#### Screen Typography (Scaling Factor: 1.2x)
```
Title: 24pt (20pt × 1.2)
Subtitle: 17pt (14pt × 1.2)
Section Headers: 14pt (12pt × 1.2)
Table Headers: 12pt (10pt × 1.2)
Body Text: 11pt (9pt × 1.2)
Small Text: 10pt (8pt × 1.2)
Currency: 11pt Monospace
```

### Optimized Column Layout

#### Items Table - Print Optimized Widths
```
Total Available: 170mm (Safety Zone)

Column Allocations:
- 項次 (Index): 15mm (8.8%)
- 品名 (Item Name): 45mm (26.5%) - Increased
- 規格 (Specification): 30mm (17.6%) - Compressed  
- 型號 (Model): 25mm (14.7%) - Compressed
- 數量 (Quantity): 15mm (8.8%)
- 單位 (Unit): 12mm (7.1%)
- 單價 (Price): 18mm (10.6%)
- 小計 (Subtotal): 18mm (10.6%)
- 備註 (Notes): 12mm (7.1%) - Minimized

Key Optimizations:
- Increased space for item names (primary identifier)
- Compressed specification and model (secondary info)
- Consistent spacing for numerical columns
- Removed excessive padding
```

### Content Fitting Strategy

#### Vertical Space Allocation (240mm Safety Zone)
```
Company Header: 35mm (14.6%)
Supplier Info Table: 25mm (10.4%)
Section Header: 8mm (3.3%)
Items Table: 120mm (50.0%) - Up to 12 items
Totals Section: 15mm (6.3%)
Terms Section: 25mm (10.4%)
Signature Section: 12mm (5.0%)
```

#### Multi-page Handling
- **Page 1**: Essential purchase order content
- **Page 2**: Overflow items + extended terms if needed
- **Page Break Logic**: Avoid breaking items table rows
- **Continuation**: Clear "Continued..." indicators

### Currency Display Optimization

#### Print Format
```
Current: "NT$ 123,456"
Optimized: "$123,456" (40% space savings)
Alternative: "123,456" with column header "金額(NT$)"
```

#### Alignment Strategy
```
Right-aligned in columns
Monospace font for consistent digit spacing
Thousands separator for readability
Decimal handling: Show .00 only when necessary
```

## Enhanced User Experience Features

### 1. Smart Preview Controls

#### Zoom and Navigation
```
Zoom Levels: 50%, 75%, 100%, 125%, 150%
Fit to Width: Automatic scaling for optimal viewing
Page Navigation: Previous/Next with keyboard shortcuts
Full Screen: Distraction-free preview mode
```

#### View Options
```
Show Print Boundaries: Toggle visible margins
Show Safe Zone: Content safety area visualization  
Show Page Numbers: Footer page indicators
Show Rulers: Measurement guides for fine-tuning
```

### 2. Intelligent Content Management

#### Dynamic Content Adjustment
- **Auto-scaling**: Content automatically adjusts for optimal fit
- **Overflow Detection**: Warns when content exceeds page boundaries
- **Smart Breaks**: Intelligent page break suggestions
- **Content Prioritization**: Essential vs. optional content identification

#### Template System Enhancement
```
Standard Template: Default business terms
Urgent Template: Expedited delivery terms
Custom Template: User-defined terms with history
Smart Suggestions: AI-powered term recommendations
```

### 3. Accessibility Improvements

#### Screen Readers
- Semantic HTML structure
- ARIA labels for all interactive elements
- Table headers properly associated
- Status announcements for state changes

#### Keyboard Navigation
- Tab order optimization
- Keyboard shortcuts for common actions
- Focus management in modal
- Escape key handling

#### Visual Accessibility
- High contrast mode support
- Text scaling up to 200%
- Color-blind friendly status indicators
- Print preview with screen reader descriptions

### 4. Performance Optimization

#### Rendering Performance
```
Virtual Scrolling: For large item lists
Lazy Loading: Non-critical content loaded on demand
Image Optimization: Logo and assets compressed
CSS Containment: Isolated rendering contexts
```

#### Print Performance
```
Pre-rendering: Generate print layouts in background  
Smart Caching: Cache formatted content
Progressive Enhancement: Basic print fallbacks
Browser Optimization: Specific CSS for different browsers
```

## Technical Implementation Guidelines

### CSS Architecture

#### Print-First CSS Structure
```scss
// 1. Base print styles
@media print {
  @page { size: A4 portrait; margin: 15mm 10mm 20mm 10mm; }
  // Core print layout
}

// 2. Screen adaptations
@media screen {
  // Enhanced screen experience
  .preview-container.print-preview {
    // A4 simulation
  }
}

// 3. Responsive adjustments
@media screen and (max-width: 768px) {
  // Mobile optimizations
}
```

#### Component Structure
```
PreviewModal/
├── PreviewHeader.vue (Title, controls, status)
├── PreviewNavigation.vue (Mode tabs, zoom controls)
├── PreviewContent.vue (Main document content)
│   ├── CompanyHeader.vue
│   ├── SupplierInfo.vue  
│   ├── ItemsTable.vue (Optimized columns)
│   ├── TotalsSection.vue
│   ├── TermsSection.vue
│   └── SignatureArea.vue
├── PreviewControls.vue (Print, export, settings)
└── PreviewFooter.vue (Actions, status)
```

### State Management

#### Preview State
```typescript
interface PreviewState {
  mode: 'edit' | 'preview' | 'export'
  zoom: number
  currentPage: number
  totalPages: number
  showBoundaries: boolean
  showSafeZone: boolean
  printSettings: PrintSettings
  contentFit: 'auto' | 'manual'
}
```

#### Print Settings
```typescript  
interface PrintSettings {
  paperSize: 'A4' | 'Letter'
  orientation: 'portrait' | 'landscape'  
  margins: Margins
  scale: number
  headers: boolean
  footers: boolean
}
```

### Error Handling and Edge Cases

#### Content Overflow Management
1. **Detection**: Real-time content measurement
2. **Warning**: Visual indicators for overflow
3. **Solutions**: Auto-scaling, font adjustment, content prioritization
4. **Fallback**: Multi-page layout with proper breaks

#### Print Compatibility
1. **Browser Testing**: Chrome, Firefox, Edge, Safari
2. **Printer Testing**: Common office printers
3. **PDF Generation**: Consistent output across platforms
4. **Fallback Styles**: Graceful degradation for unsupported features

## Implementation Phases

### Phase 1: Core Print Optimization (Week 1-2)
- [ ] A4 layout restructure
- [ ] Typography system implementation  
- [ ] Column width optimization
- [ ] Basic print preview mode

### Phase 2: Enhanced UX (Week 3-4)
- [ ] Multi-view mode implementation
- [ ] Zoom and navigation controls
- [ ] Responsive design updates
- [ ] Accessibility improvements

### Phase 3: Advanced Features (Week 5-6)
- [ ] Smart content management
- [ ] Template system enhancement
- [ ] Performance optimizations
- [ ] Cross-browser testing

### Phase 4: Polish and Testing (Week 7-8)
- [ ] User acceptance testing
- [ ] Print quality verification
- [ ] Mobile experience refinement
- [ ] Documentation and training

## Success Metrics

### Print Quality Metrics
- Content fits within A4 boundaries: 100%
- Text readability (minimum 9pt): Pass
- Table column optimization: 90% space utilization
- Print time: < 30 seconds from preview

### User Experience Metrics  
- Modal load time: < 2 seconds
- Preview mode switch: < 1 second
- Print preview accuracy: 98%+
- Mobile usability score: 85+

### Business Impact
- Print error reduction: 75%
- User satisfaction increase: 40%
- Support ticket reduction: 60%
- Training time decrease: 50%

## Conclusion

This UX specification provides a comprehensive redesign of the Purchase Order Preview Modal, addressing all identified issues while significantly enhancing the user experience. The print-first approach ensures professional document output while the enhanced screen experience improves daily workflow efficiency.

The phased implementation approach allows for iterative improvement and testing, ensuring a successful deployment that meets both user needs and business requirements.