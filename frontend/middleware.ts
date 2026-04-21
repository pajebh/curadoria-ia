import { type NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.API_URL ?? 'http://localhost:8000';

export async function middleware(req: NextRequest): Promise<NextResponse> {
  if (req.cookies.has('session_token')) {
    return NextResponse.next();
  }

  try {
    const res = await fetch(`${API_URL}/v1/sessoes`, { method: 'POST' });
    const setCookie = res.headers.get('set-cookie');
    const response = NextResponse.next();
    if (setCookie) {
      response.headers.set('set-cookie', setCookie);
    }
    return response;
  } catch {
    // Se o backend estiver indisponível, deixa passar sem sessão
    return NextResponse.next();
  }
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon\\.ico|api/health).*)'],
};
