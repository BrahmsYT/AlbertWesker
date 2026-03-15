'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { onAuthStateChanged, User, signInWithPopup, signOut } from 'firebase/auth';
import { doc, getDoc, setDoc, collection, query, where, getDocs } from 'firebase/firestore';
import { auth, db, googleProvider, handleFirestoreError, OperationType } from '@/lib/firebase';
import { useRouter, usePathname } from 'next/navigation';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  organization: any | null;
  role: string | null;
  globalRole: string | null;
  signIn: () => Promise<void>;
  logOut: () => Promise<void>;
  setOrganization: (org: any, role: string) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  organization: null,
  role: null,
  globalRole: null,
  signIn: async () => {},
  logOut: async () => {},
  setOrganization: () => {},
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [organization, setOrg] = useState<any | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [globalRole, setGlobalRole] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      if (currentUser) {
        try {
          // Check if user exists in DB
          const userRef = doc(db, 'users', currentUser.uid);
          const userSnap = await getDoc(userRef);
          
          let userData: any;
          if (!userSnap.exists()) {
            userData = {
              uid: currentUser.uid,
              email: currentUser.email,
              displayName: currentUser.displayName,
              photoURL: currentUser.photoURL,
              role: currentUser.email === 'qasimlirenat@gmail.com' ? 'admin' : 'user',
              createdAt: new Date().toISOString(),
            };
            await setDoc(userRef, userData);
          } else {
            userData = userSnap.data();
            // Bootstrap admin role if email matches but role is not set
            if (currentUser.email === 'qasimlirenat@gmail.com' && userData.role !== 'admin') {
              await setDoc(userRef, { ...userData, role: 'admin' }, { merge: true });
              userData.role = 'admin';
            }
          }
          setGlobalRole(userData.role || 'user');

          // Check memberships
          const membershipsRef = collection(db, 'memberships');
          const q = query(membershipsRef, where('userId', '==', currentUser.uid));
          const membershipsSnap = await getDocs(q);
          
          if (!membershipsSnap.empty) {
            const membership = membershipsSnap.docs[0].data();
            const orgRef = doc(db, 'organizations', membership.organizationId);
            const orgSnap = await getDoc(orgRef);
            if (orgSnap.exists()) {
              setOrg({ id: orgSnap.id, ...orgSnap.data() });
              setRole(membership.role);
            }
          } else {
            if (pathname !== '/onboarding' && pathname !== '/' && userData.role !== 'admin') {
              router.push('/onboarding');
            }
          }
        } catch (error) {
          console.error('Error fetching user data:', error);
        }
      } else {
        setOrg(null);
        setRole(null);
        setGlobalRole(null);
        if (pathname !== '/' && pathname !== '/login') {
          router.push('/');
        }
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, [pathname, router]);

  const signIn = async () => {
    try {
      await signInWithPopup(auth, googleProvider);
      router.push('/dashboard');
    } catch (error) {
      console.error('Error signing in:', error);
    }
  };

  const logOut = async () => {
    try {
      await signOut(auth);
      router.push('/');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const setOrganization = (org: any, newRole: string) => {
    setOrg(org);
    setRole(newRole);
  };

  return (
    <AuthContext.Provider value={{ user, loading, organization, role, globalRole, signIn, logOut, setOrganization }}>
      {children}
    </AuthContext.Provider>
  );
}
