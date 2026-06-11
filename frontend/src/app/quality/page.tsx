import { ArrowLeft, FlaskConical, Scale, SplitSquareHorizontal } from 'lucide-react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { StatPill } from '../../components/ui/StatPill';
import { TopNav } from '../../components/ui/TopNav';
import { abTestingSummary, datasetShape, goldenSample, rubricBaseline } from '../../lib/data/evalData';
import styles from './page.module.css';

export const metadata: Metadata = {
  title: 'Evals & Quality | Lyrio',
  description: 'Golden dataset, LLM-judge rubrics, and A/B testing methodology',
};

const difficultyVariant = { easy: 'success', medium: 'warning', hard: 'primary' } as const;

export default function QualityPage() {
  return (
    <div>
      <TopNav
        left={
          <div className={styles.brand}>
            <div className={styles.logoBadge}>
              <FlaskConical size={18} />
            </div>
            <div>
              <h1 className={styles.brandTitle}>Evals &amp; Quality</h1>
              <p className={styles.brandSubtitle}>Golden dataset, LLM-judge rubrics, A/B methodology</p>
            </div>
          </div>
        }
        right={
          <div className={styles.navRight}>
            <StatPill label="Golden cases" value={`${datasetShape.total}`} />
            <StatPill label="Judge rubrics" value="4" />
            <Link href="/">
              <Button variant="ghost" icon={<ArrowLeft size={16} />}>
                Console
              </Button>
            </Link>
          </div>
        }
      />

      <main className={styles.shell}>
        <Card variant="surface" className={styles.section}>
          <SectionHeader
            title="Nightly LLM-judge baseline"
            subtitle="evals/judge.py scores every golden case against four rubrics; CI gates on regression vs evals/baseline.json"
            action={<Scale size={16} color="var(--lyr-color-text-muted)" />}
          />
          <div className={styles.rubricGrid}>
            {rubricBaseline.map((rubric) => (
              <Card key={rubric.rubric} variant="surface" className={styles.rubricCard}>
                <span className={styles.rubricScore}>{(rubric.score * 100).toFixed(0)}%</span>
                <strong className={styles.rubricName}>{rubric.rubric}</strong>
                <p className={styles.rubricDetail}>{rubric.detail}</p>
              </Card>
            ))}
          </div>
        </Card>

        <Card variant="surface" className={styles.section}>
          <SectionHeader
            title="Golden dataset sample"
            subtitle={`${datasetShape.total} hand-curated cases — 5 shown here, full set in evals/golden_dataset.json`}
          />
          <div className={styles.caseList}>
            {goldenSample.map((goldenCase) => (
              <Card key={goldenCase.id} variant="surface" className={styles.caseCard}>
                <div className={styles.caseHeader}>
                  <Badge variant="neutral">{goldenCase.id}</Badge>
                  <Badge variant={difficultyVariant[goldenCase.difficulty]}>{goldenCase.difficulty}</Badge>
                  <Badge variant="neutral">{goldenCase.category}</Badge>
                  <Badge variant="neutral">{goldenCase.botType} bot</Badge>
                </div>
                <p className={styles.caseInput}>&ldquo;{goldenCase.input}&rdquo;</p>
                <p className={styles.caseExpectation}>{goldenCase.expectation}</p>
              </Card>
            ))}
          </div>
          <div className={styles.distributionRow}>
            {datasetShape.byCategory.map((bucket) => (
              <Badge key={bucket.label} variant="neutral">
                {bucket.label}: {bucket.count}
              </Badge>
            ))}
          </div>
        </Card>

        <Card variant="surface" className={styles.section}>
          <SectionHeader
            title="A/B testing"
            subtitle={abTestingSummary.source}
            action={<SplitSquareHorizontal size={16} color="var(--lyr-color-text-muted)" />}
          />
          <div className={styles.abGrid}>
            <div className={styles.abMethod}>
              <p>
                <strong>Bucketing:</strong> {abTestingSummary.bucketing}
              </p>
              <p>
                <strong>Significance:</strong> {abTestingSummary.significance}
              </p>
            </div>
            <Card variant="surface" className={styles.abExperiment}>
              <strong>{abTestingSummary.exampleExperiment.name}</strong>
              <div className={styles.abVariants}>
                {[abTestingSummary.exampleExperiment.variantA, abTestingSummary.exampleExperiment.variantB].map(
                  (variant) => (
                    <div key={variant.label} className={styles.abVariant}>
                      <span>{variant.label}</span>
                      <div className={styles.abBarTrack}>
                        <div className={styles.abBarFill} style={{ width: `${variant.conversion * 100}%` }} />
                      </div>
                      <span className={styles.abPct}>{Math.round(variant.conversion * 100)}%</span>
                    </div>
                  ),
                )}
              </div>
              <p className={styles.abVerdict}>{abTestingSummary.exampleExperiment.verdict}</p>
            </Card>
          </div>
        </Card>
      </main>
    </div>
  );
}
