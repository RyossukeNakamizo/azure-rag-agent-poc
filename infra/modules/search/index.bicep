// ================================================================
// Azure AI Search Index Module
// Purpose: RAG用Index Schema定義（Vector + Hybrid Search対応）
// ================================================================

@description('Azure AI Search サービス名')
param searchServiceName string

@description('Index名')
param indexName string = 'rag-docs-index'


// ================================================================
// 既存Search Serviceへの参照
// ================================================================
resource searchService 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: searchServiceName
}

// ================================================================
// Index定義
// ================================================================
resource searchIndex 'Microsoft.Search/searchServices/indexes@2023-11-01' = {
  parent: searchService
  name: indexName
  properties: {
    fields: [
      // Primary Key
      {
        name: 'id'
        type: 'Edm.String'
        key: true
        searchable: false
        filterable: false
        sortable: false
        facetable: false
      }
      // Content（検索対象テキスト）
      {
        name: 'content'
        type: 'Edm.String'
        searchable: true
        filterable: false
        sortable: false
        facetable: false
        analyzer: 'ja.microsoft'
      }
      // Filename（ファイル名、フィルタリング可）
      {
        name: 'filename'
        type: 'Edm.String'
        searchable: true
        filterable: true
        sortable: true
        facetable: true
      }
      // URL（ソース追跡用）
      {
        name: 'url'
        type: 'Edm.String'
        searchable: false
        filterable: true
        sortable: false
        facetable: false
      }
      // Category（カテゴリ分類）
      {
        name: 'category'
        type: 'Edm.String'
        searchable: true
        filterable: true
        sortable: false
        facetable: true
      }
      // Content Vector（1536次元、text-embedding-ada-002）
      {
        name: 'contentVector'
        type: 'Collection(Edm.Single)'
        searchable: true
        filterable: false
        sortable: false
        facetable: false
        dimensions: 1536
        vectorSearchProfile: 'rag-vector-profile'
      }
    ]
    
    vectorSearch: {
      algorithms: [
        {
          name: 'rag-hnsw-algorithm'
          kind: 'hnsw'
          hnswParameters: {
            m: 4
            efConstruction: 400
            efSearch: 500
            metric: 'cosine'
          }
        }
      ]
      profiles: [
        {
          name: 'rag-vector-profile'
          algorithm: 'rag-hnsw-algorithm'
        }
      ]
    }
    
    semantic: {
      configurations: [
        {
          name: 'rag-semantic-config'
          prioritizedFields: {
            titleField: {
              fieldName: 'filename'
            }
            contentFields: [
              {
                fieldName: 'content'
              }
            ]
            keywordsFields: [
              {
                fieldName: 'category'
              }
            ]
          }
        }
      ]
    }
  }
}

output indexName string = searchIndex.name
output searchServiceEndpoint string = 'https://${searchService.name}.search.windows.net'
