import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002/api';
  
  try {
    const projectsResponse = await fetch(`${apiUrl}/projects?page=1&page_size=5`);
    const projectsData = await projectsResponse.json();
    
    const historyResponse = await fetch(`${apiUrl}/project-history?page=1&page_size=5`);
    const historyData = await historyResponse.json();
    
    res.status(200).json({
      success: true,
      apiUrl,
      projects: projectsData,
      history: historyData
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      apiUrl,
      error: error instanceof Error ? error.message : String(error)
    });
  }
}
