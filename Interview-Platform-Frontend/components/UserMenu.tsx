"use client";

import { useEffect, useMemo, useState } from "react";
import { getUserInfo } from "@/utils/api/user";
import type { UserInfoResponse } from "@/types/api";


export function UserMenu() {
  const [user, setUser] = useState<UserInfoResponse | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;

    getUserInfo()
      .then((response) => {
        if (isMounted) {
          setUser(response);
        }
      })
      .catch(() => {
        if (isMounted) {
          setUser(null);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const displayName = useMemo(() => {
    return user?.name || user?.email?.split("@")[0] || "User";
  }, [user]);

  if (!user) {
    return null;
  }

  return (
    <div className="user-menu">
      <button
        className="user-menu-trigger"
        type="button"
        aria-label="User account"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((currentValue) => !currentValue)}
      >
        {user.picture_url ? (
          <img
            alt=""
            src={user.picture_url}
            referrerPolicy="no-referrer"
          />
        ) : (
          <span>{displayName.charAt(0).toUpperCase()}</span>
        )}
      </button>

      {isOpen ? (
        <div className="user-menu-popover">
          <div className="user-menu-profile">
            {user.picture_url ? (
              <img
                alt=""
                src={user.picture_url}
                referrerPolicy="no-referrer"
              />
            ) : (
              <span>{displayName.charAt(0).toUpperCase()}</span>
            )}
            <div>
              <strong>{displayName}</strong>
              <small>{user.email}</small>
            </div>
          </div>

          <dl className="user-menu-details">
            <div>
              <dt>User ID</dt>
              <dd>{user.id}</dd>
            </div>
          </dl>
        </div>
      ) : null}
    </div>
  );
}
