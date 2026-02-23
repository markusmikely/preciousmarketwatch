import { useState, useEffect } from 'react';
import { client } from '@/lib/graphql';
import { TypedDocumentNode } from 'graphql-request';

interface UseGraphQLOptions {
  skip?: boolean;
  variables?: Record<string, any>;
}

interface UseGraphQLResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

/**
 * Custom hook for GraphQL queries with built-in error handling and loading states
 * @param query - GraphQL query document
 * @param options - Skip flag and GraphQL variables
 * @returns data, loading, error, and refetch function
 */
export function useGraphQL<T>(
  query: TypedDocumentNode,
  options?: UseGraphQLOptions
): UseGraphQLResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = async () => {
    // Skip if explicitly requested
    if (options?.skip) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await client.request<T>(query, options?.variables || {});
      setData(result);
      setLoading(false);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      console.error('[useGraphQL] Error fetching data:', error);
      setError(error);
      setLoading(false);
      // Keep existing data on error (graceful degradation)
    }
  };

  const refetch = async () => {
    await fetchData();
  };

  useEffect(() => {
    fetchData();
  }, [JSON.stringify(options?.variables || {})]);

  return { data, loading, error, refetch };
}

/**
 * Hook variant for simpler use cases with just query document
 */
export function useGraphQLQuery<T>(
  query: TypedDocumentNode,
  variables?: Record<string, any>
): UseGraphQLResult<T> {
  return useGraphQL<T>(query, { variables });
}
