/* global use, db */
// MongoDB Playground: borrar registros de desarrollo por fecha

const DB_NAME = 'bdo_asset_tracker';
const COLLECTION_NAME = 'records';
const DATE_FIELD = 'captured_at';
const CUTOFF_ISO = '2026-03-15T17:00:00';
const CUTOFF_DATE = new Date('2026-03-15T17:00:00Z');
const DRY_RUN = false; // true = solo contar; false = borrar

use(DB_NAME);

console.log(`\n🧹 Limpieza en DB: ${db.getName()}`);
console.log(`Colección objetivo: ${COLLECTION_NAME}`);
console.log(`Campo fecha: ${DATE_FIELD}`);
console.log(`Corte (string): ${CUTOFF_ISO}`);
console.log(`Corte (date): ${CUTOFF_DATE.toISOString()}`);
console.log(`Modo: ${DRY_RUN ? 'DRY_RUN (sin borrar)' : 'DELETE (borra registros)'}\n`);

const collection = db.getCollection(COLLECTION_NAME);

const filter = {
  $or: [
    { [DATE_FIELD]: { $type: 'string', $lt: CUTOFF_ISO } },
    { [DATE_FIELD]: { $type: 'date', $lt: CUTOFF_DATE } },
  ],
};

const matching = collection.countDocuments(filter);
let deleted = 0;

if (!DRY_RUN && matching > 0) {
  const result = collection.deleteMany(filter);
  deleted = result.deletedCount ?? 0;
}

const report = {
  collection: COLLECTION_NAME,
  matching,
  deleted,
};

console.log('Resultado:');
console.log(`- ${report.collection}: candidatos=${report.matching}, borrados=${report.deleted}`);

report;
