const DB_NAME = 'bdo_asset_tracker';
use(DB_NAME);

console.log(`\n📦 Base de datos activa: ${db.getName()}\n`);

// 1) Listar colecciones
const collectionNames = db.getCollectionNames().sort();
console.log(`Colecciones encontradas (${collectionNames.length}):`);
collectionNames.forEach((name, idx) => console.log(`${idx + 1}. ${name}`));

// 2) Resumen por colección (documentos + stats básicas + muestra)
const summary = collectionNames.map((collectionName) => {
  const collection = db.getCollection(collectionName);
  const documentCount = collection.estimatedDocumentCount();

  let storageStats = null;
  try {
    storageStats = db.runCommand({ collStats: collectionName });
  } catch (error) {
    storageStats = { ok: 0, error: error.message };
  }

  const sampleDocs = collection.find({}).limit(3).toArray();

  return {
    collection: collectionName,
    estimatedDocuments: documentCount,
    sizeBytes: storageStats?.size ?? null,
    storageSizeBytes: storageStats?.storageSize ?? null,
    avgObjSizeBytes: storageStats?.avgObjSize ?? null,
    indexes: storageStats?.nindexes ?? null,
    sample: sampleDocs,
  };
});

console.log('\n🔎 Resumen por colección:\n');
summary.forEach((item) => {
  console.log(`- ${item.collection}`);
  console.log(`  docs~: ${item.estimatedDocuments}`);
  console.log(`  size: ${item.sizeBytes} bytes | storage: ${item.storageSizeBytes} bytes | indexes: ${item.indexes}`);
});

// 3) Devuelve el objeto completo para inspección en Results
summary;
