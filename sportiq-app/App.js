import { useState, useEffect } from 'react';
import {
  StyleSheet, Text, View, ScrollView,
  TouchableOpacity, ActivityIndicator, RefreshControl
} from 'react-native';
import { getTodayMatches, getTeamStats, predictMatch } from './services';

const STARS = (n) => '⭐'.repeat(n) + '☆'.repeat(5 - n);

const SPORTS = [
  { key: 'football', label: '⚽ Football' },
  { key: 'basketball', label: '🏀 Basketball' },
  { key: 'tennis', label: '🎾 Tennis' },
];

export default function App() {
  const [sport, setSport] = useState('football');
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selected, setSelected] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [predicting, setPredicting] = useState(false);

  useEffect(() => { loadMatches(); }, [sport]);

  const loadMatches = async () => {
    setLoading(true);
    setSelected(null);
    setPrediction(null);
    try {
      const data = await getTodayMatches(sport);
      setMatches(data);
    } catch (e) {
      console.error(e);
      setMatches([]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadMatches();
    setRefreshing(false);
  };

  const analyze = async (match) => {
    setSelected(match);
    setPrediction(null);
    setPredicting(true);
    try {
      const stats = await getTeamStats(match.team_home, match.team_away, sport);
      const pred = await predictMatch(match, stats, sport);
      setPrediction(pred);
    } catch (e) {
      setPrediction({ error: e.message });
    } finally {
      setPredicting(false);
    }
  };

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('fr-FR', {
      weekday: 'short', day: 'numeric',
      month: 'short', hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#00ff88" />}
    >
      <View style={styles.header}>
        <Text style={styles.logo}>🏆 Sportiq</Text>
        <Text style={styles.subtitle}>Matchs du jour</Text>
      </View>

      <View style={styles.tabs}>
        {SPORTS.map(s => (
          <TouchableOpacity
            key={s.key}
            style={[styles.tab, sport === s.key && styles.tabActive]}
            onPress={() => setSport(s.key)}
          >
            <Text style={[styles.tabText, sport === s.key && styles.tabTextActive]}>
              {s.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading && <ActivityIndicator size="large" color="#00ff88" style={{ margin: 30 }} />}

      {!loading && !selected && (
        <>
          <Text style={styles.sectionTitle}>{matches.length} match(s)</Text>
          {matches.map((m, i) => (
            <TouchableOpacity key={i} style={styles.card} onPress={() => analyze(m)}>
              <Text style={styles.league}>{m.league?.replace(/_/g, ' ').toUpperCase()}</Text>
              <View style={styles.row}>
                <Text style={styles.team}>{m.team_home}</Text>
                <Text style={styles.vs}>VS</Text>
                <Text style={styles.team}>{m.team_away}</Text>
              </View>
              <Text style={styles.date}>{formatDate(m.commence_time)}</Text>
              {m.odds?.home_odds && (
                <View style={styles.oddsRow}>
                  <View style={styles.oddBox}>
                    <Text style={styles.oddLabel}>1</Text>
                    <Text style={styles.oddValue}>{m.odds.home_odds}</Text>
                  </View>
                  {m.odds.draw_odds && (
                    <View style={styles.oddBox}>
                      <Text style={styles.oddLabel}>N</Text>
                      <Text style={styles.oddValue}>{m.odds.draw_odds}</Text>
                    </View>
                  )}
                  <View style={styles.oddBox}>
                    <Text style={styles.oddLabel}>2</Text>
                    <Text style={styles.oddValue}>{m.odds.away_odds}</Text>
                  </View>
                </View>
              )}
              <Text style={styles.analyzeHint}>🔍 Analyser →</Text>
            </TouchableOpacity>
          ))}
        </>
      )}

      {selected && predicting && (
        <View style={styles.card}>
          <Text style={styles.matchTitle}>{selected.team_home} vs {selected.team_away}</Text>
          <ActivityIndicator size="large" color="#00ff88" style={{ margin: 20 }} />
          <Text style={{ color: '#666', textAlign: 'center' }}>Analyse IA en cours...</Text>
        </View>
      )}

      {selected && prediction && !predicting && (
        <View>
          <TouchableOpacity onPress={() => { setSelected(null); setPrediction(null); }}>
            <Text style={styles.back}>← Retour</Text>
          </TouchableOpacity>

          <View style={styles.card}>
            <Text style={styles.matchTitle}>{prediction.match}</Text>
            <Text style={styles.analyse}>{prediction.analyse}</Text>
          </View>

          {selected.odds?.home_odds && (
            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Cotes</Text>
              <View style={styles.oddsRow}>
                <View style={styles.oddBoxLarge}>
                  <Text style={styles.oddLabel}>{selected.team_home}</Text>
                  <Text style={styles.oddValueLarge}>{selected.odds.home_odds}</Text>
                </View>
                {selected.odds.draw_odds && (
                  <View style={styles.oddBoxLarge}>
                    <Text style={styles.oddLabel}>Nul</Text>
                    <Text style={styles.oddValueLarge}>{selected.odds.draw_odds}</Text>
                  </View>
                )}
                <View style={styles.oddBoxLarge}>
                  <Text style={styles.oddLabel}>{selected.team_away}</Text>
                  <Text style={styles.oddValueLarge}>{selected.odds.away_odds}</Text>
                </View>
              </View>
            </View>
          )}

          <Text style={styles.sectionTitle}>Prédictions IA</Text>
          {Object.entries(prediction.predictions || {}).map(([key, val]) => (
            <View key={key} style={styles.predCard}>
              <View style={styles.row}>
                <Text style={styles.predName}>{key.toUpperCase()}</Text>
                <Text>{STARS(val.stars)}</Text>
              </View>
              <Text style={styles.predResult}>→ {val.result}</Text>
              <Text style={styles.predConf}>Confiance : {val.confidence_pct}%</Text>
              <Text style={styles.predReason}>{val.reasoning}</Text>
            </View>
          ))}
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a1a', padding: 16 },
  header: { alignItems: 'center', paddingVertical: 24 },
  logo: { fontSize: 28, fontWeight: 'bold', color: '#00ff88' },
  subtitle: { fontSize: 13, color: '#666', marginTop: 4 },
  tabs: { flexDirection: 'row', marginBottom: 16 },
  tab: { flex: 1, padding: 10, borderRadius: 8, backgroundColor: '#1a1a2e', marginHorizontal: 3, alignItems: 'center' },
  tabActive: { backgroundColor: '#00ff88' },
  tabText: { color: '#aaa', fontSize: 12, fontWeight: 'bold' },
  tabTextActive: { color: '#0a0a1a' },
  sectionTitle: { color: '#00ff88', fontSize: 14, fontWeight: 'bold', marginVertical: 10 },
  card: { backgroundColor: '#1a1a2e', borderRadius: 12, padding: 14, marginBottom: 10 },
  league: { color: '#555', fontSize: 10, marginBottom: 6 },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  team: { color: '#fff', fontWeight: 'bold', fontSize: 13, flex: 1 },
  vs: { color: '#444', fontSize: 12, marginHorizontal: 8 },
  date: { color: '#555', fontSize: 11, marginTop: 4, marginBottom: 8 },
  oddsRow: { flexDirection: 'row', justifyContent: 'space-around', marginTop: 8 },
  oddBox: { backgroundColor: '#0a0a1a', borderRadius: 6, padding: 6, alignItems: 'center', minWidth: 55 },
  oddBoxLarge: { backgroundColor: '#0a0a1a', borderRadius: 8, padding: 10, alignItems: 'center', flex: 1, marginHorizontal: 4 },
  oddLabel: { color: '#666', fontSize: 10 },
  oddValue: { color: '#00ff88', fontWeight: 'bold', fontSize: 14 },
  oddValueLarge: { color: '#00ff88', fontWeight: 'bold', fontSize: 22 },
  analyzeHint: { color: '#00ff88', fontSize: 12, marginTop: 8, textAlign: 'right' },
  back: { color: '#00ff88', fontSize: 14, marginBottom: 12 },
  matchTitle: { fontSize: 18, fontWeight: 'bold', color: '#fff', textAlign: 'center', marginBottom: 8 },
  analyse: { color: '#aaa', textAlign: 'center', lineHeight: 20, fontSize: 13 },
  predCard: { backgroundColor: '#1a1a2e', borderRadius: 12, padding: 14, marginBottom: 8 },
  predName: { color: '#fff', fontWeight: 'bold', fontSize: 13 },
  predResult: { color: '#00ff88', fontSize: 16, fontWeight: 'bold', marginVertical: 4 },
  predConf: { color: '#aaa', fontSize: 12, marginBottom: 4 },
  predReason: { color: '#666', fontSize: 11 },
});