import React from "react";

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  style?: React.CSSProperties;
}

export function Skeleton({ width = "100%", height = 20, borderRadius = 8, style }: SkeletonProps) {
  return (
    <div style={{
      width, height, borderRadius,
      background: "linear-gradient(90deg, rgba(255,255,255,.04) 25%, rgba(255,255,255,.08) 50%, rgba(255,255,255,.04) 75%)",
      backgroundSize: "200% 100%",
      animation: "shimmer 1.5s infinite",
      ...style,
    }}>
      <style>{`
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
}

// 캐릭터 카드 스켈레톤
export function CharacterCardSkeleton() {
  return (
    <div style={{
      borderRadius: 20, overflow: "hidden",
      border: "1px solid var(--border-default)",
      background: "rgba(17,21,40,.7)",
      minWidth: 180,
    }}>
      <Skeleton height={200} borderRadius={0} />
      <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column", gap: 8 }}>
        <Skeleton height={16} width="60%" borderRadius={6} />
        <Skeleton height={13} width="90%" borderRadius={6} />
        <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
          <Skeleton height={22} width={50} borderRadius={999} />
          <Skeleton height={22} width={50} borderRadius={999} />
        </div>
      </div>
    </div>
  );
}

// 캐릭터 카드 그리드 스켈레톤
export function CharacterGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 20 }}>
      {Array.from({ length: count }).map((_, i) => (
        <CharacterCardSkeleton key={i} />
      ))}
    </div>
  );
}

// 리스트 아이템 스켈레톤
export function ListItemSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{
          borderRadius: 16, padding: "16px 20px",
          border: "1px solid var(--border-default)",
          background: "rgba(17,21,40,.7)",
          display: "flex", alignItems: "center", gap: 16,
        }}>
          <Skeleton width={52} height={52} borderRadius="50%" />
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
            <Skeleton height={16} width="40%" borderRadius={6} />
            <Skeleton height={13} width="70%" borderRadius={6} />
          </div>
        </div>
      ))}
    </div>
  );
}

// 프로필 스켈레톤
export function ProfileSkeleton() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
      <Skeleton width={80} height={80} borderRadius="50%" />
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <Skeleton height={20} width={120} borderRadius={6} />
        <Skeleton height={14} width={160} borderRadius={6} />
        <Skeleton height={13} width={100} borderRadius={6} />
      </div>
    </div>
  );
}

// 배너 스켈레톤
export function BannerSkeleton() {
  return <Skeleton height={180} borderRadius={0} />;
}

// 랭킹 아이템 스켈레톤
export function RankingItemSkeleton({ count = 10 }: { count?: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{
          display: "flex", alignItems: "center", gap: 16,
          padding: "14px 16px", borderRadius: 16,
          border: "1px solid var(--border-subtle)",
          background: "rgba(17,21,40,.5)",
        }}>
          <Skeleton width={32} height={16} borderRadius={6} />
          <Skeleton width={44} height={44} borderRadius="50%" />
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
            <Skeleton height={14} width="30%" borderRadius={6} />
            <Skeleton height={12} width="60%" borderRadius={6} />
          </div>
        </div>
      ))}
    </div>
  );
}