var s=(e,t,n)=>new Promise((o,i)=>{var r=d=>{try{u(n.next(d))}catch(p){i(p)}},a=d=>{try{u(n.throw(d))}catch(p){i(p)}},u=d=>d.done?o(d.value):Promise.resolve(d.value).then(r,a);u((n=n.apply(e,t)).next())});import{r as T,h as k,C as I,e as P,E as ee,q as j,F as _e,t as S,l as Oe,v as Ce,u as Ne,w as De,x as _}from"./index.esm2017-CqPmkKob.js";const te="@firebase/installations",F="0.6.18";/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const ne=1e4,oe=`w:${F}`,ie="FIS_v2",Re="https://firebaseinstallations.googleapis.com/v1",Me=60*60*1e3,Pe="installations",je="Installations";/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const Fe={"missing-app-config-values":'Missing App configuration value: "{$valueName}"',"not-registered":"Firebase Installation is not registered.","installation-not-found":"Firebase Installation not found.","request-failed":'{$requestName} request failed with error "{$serverCode} {$serverStatus}: {$serverMessage}"',"app-offline":"Could not process request. Application offline.","delete-pending-registration":"Can't delete installation while there is a pending registration request."},h=new ee(Pe,je,Fe);function re(e){return e instanceof _e&&e.code.includes("request-failed")}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function ae({projectId:e}){return`${Re}/projects/${e}/installations`}function se(e){return{token:e.token,requestStatus:2,expiresIn:Ke(e.expiresIn),creationTime:Date.now()}}function ce(e,t){return s(this,null,function*(){const o=(yield t.json()).error;return h.create("request-failed",{requestName:e,serverCode:o.code,serverMessage:o.message,serverStatus:o.status})})}function ue({apiKey:e}){return new Headers({"Content-Type":"application/json",Accept:"application/json","x-goog-api-key":e})}function $e(e,{refreshToken:t}){const n=ue(e);return n.append("Authorization",qe(t)),n}function de(e){return s(this,null,function*(){const t=yield e();return t.status>=500&&t.status<600?e():t})}function Ke(e){return Number(e.replace("s","000"))}function qe(e){return`${ie} ${e}`}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function Le(o,i){return s(this,arguments,function*({appConfig:e,heartbeatServiceProvider:t},{fid:n}){const r=ae(e),a=ue(e),u=t.getImmediate({optional:!0});if(u){const l=yield u.getHeartbeatsHeader();l&&a.append("x-firebase-client",l)}const d={fid:n,authVersion:ie,appId:e.appId,sdkVersion:oe},p={method:"POST",headers:a,body:JSON.stringify(d)},c=yield de(()=>fetch(r,p));if(c.ok){const l=yield c.json();return{fid:l.fid||n,registrationStatus:2,refreshToken:l.refreshToken,authToken:se(l.authToken)}}else throw yield ce("Create Installation",c)})}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function fe(e){return new Promise(t=>{setTimeout(t,e)})}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function xe(e){return btoa(String.fromCharCode(...e)).replace(/\+/g,"-").replace(/\//g,"_")}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const Ve=/^[cdef][\w-]{21}$/,M="";function Be(){try{const e=new Uint8Array(17);(self.crypto||self.msCrypto).getRandomValues(e),e[0]=112+e[0]%16;const n=He(e);return Ve.test(n)?n:M}catch(e){return M}}function He(e){return xe(e).substr(0,22)}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function A(e){return`${e.appName}!${e.appId}`}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const pe=new Map;function le(e,t){const n=A(e);ge(n,t),We(n,t)}function ge(e,t){const n=pe.get(e);if(n)for(const o of n)o(t)}function We(e,t){const n=Ue();n&&n.postMessage({key:e,fid:t}),Ge()}let w=null;function Ue(){return!w&&"BroadcastChannel"in self&&(w=new BroadcastChannel("[Firebase] FID Change"),w.onmessage=e=>{ge(e.data.key,e.data.fid)}),w}function Ge(){pe.size===0&&w&&(w.close(),w=null)}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const Je="firebase-installations-database",Ye=1,b="firebase-installations-store";let O=null;function $(){return O||(O=j(Je,Ye,{upgrade:(e,t)=>{switch(t){case 0:e.createObjectStore(b)}}})),O}function v(e,t){return s(this,null,function*(){const n=A(e),i=(yield $()).transaction(b,"readwrite"),r=i.objectStore(b),a=yield r.get(n);return yield r.put(t,n),yield i.done,(!a||a.fid!==t.fid)&&le(e,t.fid),t})}function we(e){return s(this,null,function*(){const t=A(e),o=(yield $()).transaction(b,"readwrite");yield o.objectStore(b).delete(t),yield o.done})}function E(e,t){return s(this,null,function*(){const n=A(e),i=(yield $()).transaction(b,"readwrite"),r=i.objectStore(b),a=yield r.get(n),u=t(a);return u===void 0?yield r.delete(n):yield r.put(u,n),yield i.done,u&&(!a||a.fid!==u.fid)&&le(e,u.fid),u})}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function K(e){return s(this,null,function*(){let t;const n=yield E(e.appConfig,o=>{const i=ze(o),r=Xe(e,i);return t=r.registrationPromise,r.installationEntry});return n.fid===M?{installationEntry:yield t}:{installationEntry:n,registrationPromise:t}})}function ze(e){const t=e||{fid:Be(),registrationStatus:0};return he(t)}function Xe(e,t){if(t.registrationStatus===0){if(!navigator.onLine){const i=Promise.reject(h.create("app-offline"));return{installationEntry:t,registrationPromise:i}}const n={fid:t.fid,registrationStatus:1,registrationTime:Date.now()},o=Qe(e,n);return{installationEntry:n,registrationPromise:o}}else return t.registrationStatus===1?{installationEntry:t,registrationPromise:Ze(e)}:{installationEntry:t}}function Qe(e,t){return s(this,null,function*(){try{const n=yield Le(e,t);return v(e.appConfig,n)}catch(n){throw re(n)&&n.customData.serverCode===409?yield we(e.appConfig):yield v(e.appConfig,{fid:t.fid,registrationStatus:0}),n}})}function Ze(e){return s(this,null,function*(){let t=yield W(e.appConfig);for(;t.registrationStatus===1;)yield fe(100),t=yield W(e.appConfig);if(t.registrationStatus===0){const{installationEntry:n,registrationPromise:o}=yield K(e);return o||n}return t})}function W(e){return E(e,t=>{if(!t)throw h.create("installation-not-found");return he(t)})}function he(e){return et(e)?{fid:e.fid,registrationStatus:0}:e}function et(e){return e.registrationStatus===1&&e.registrationTime+ne<Date.now()}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function tt(o,i){return s(this,arguments,function*({appConfig:e,heartbeatServiceProvider:t},n){const r=nt(e,n),a=$e(e,n),u=t.getImmediate({optional:!0});if(u){const l=yield u.getHeartbeatsHeader();l&&a.append("x-firebase-client",l)}const d={installation:{sdkVersion:oe,appId:e.appId}},p={method:"POST",headers:a,body:JSON.stringify(d)},c=yield de(()=>fetch(r,p));if(c.ok){const l=yield c.json();return se(l)}else throw yield ce("Generate Auth Token",c)})}function nt(e,{fid:t}){return`${ae(e)}/${t}/authTokens:generate`}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function q(e,t=!1){return s(this,null,function*(){let n;const o=yield E(e.appConfig,r=>{if(!be(r))throw h.create("not-registered");const a=r.authToken;if(!t&&rt(a))return r;if(a.requestStatus===1)return n=ot(e,t),r;{if(!navigator.onLine)throw h.create("app-offline");const u=st(r);return n=it(e,u),u}});return n?yield n:o.authToken})}function ot(e,t){return s(this,null,function*(){let n=yield U(e.appConfig);for(;n.authToken.requestStatus===1;)yield fe(100),n=yield U(e.appConfig);const o=n.authToken;return o.requestStatus===0?q(e,t):o})}function U(e){return E(e,t=>{if(!be(t))throw h.create("not-registered");const n=t.authToken;return ct(n)?Object.assign(Object.assign({},t),{authToken:{requestStatus:0}}):t})}function it(e,t){return s(this,null,function*(){try{const n=yield tt(e,t),o=Object.assign(Object.assign({},t),{authToken:n});return yield v(e.appConfig,o),n}catch(n){if(re(n)&&(n.customData.serverCode===401||n.customData.serverCode===404))yield we(e.appConfig);else{const o=Object.assign(Object.assign({},t),{authToken:{requestStatus:0}});yield v(e.appConfig,o)}throw n}})}function be(e){return e!==void 0&&e.registrationStatus===2}function rt(e){return e.requestStatus===2&&!at(e)}function at(e){const t=Date.now();return t<e.creationTime||e.creationTime+e.expiresIn<t+Me}function st(e){const t={requestStatus:1,requestTime:Date.now()};return Object.assign(Object.assign({},e),{authToken:t})}function ct(e){return e.requestStatus===1&&e.requestTime+ne<Date.now()}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function ut(e){return s(this,null,function*(){const t=e,{installationEntry:n,registrationPromise:o}=yield K(t);return o?o.catch(console.error):q(t).catch(console.error),n.fid})}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function dt(e,t=!1){return s(this,null,function*(){const n=e;return yield ft(n),(yield q(n,t)).token})}function ft(e){return s(this,null,function*(){const{registrationPromise:t}=yield K(e);t&&(yield t)})}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function pt(e){if(!e||!e.options)throw C("App Configuration");if(!e.name)throw C("App Name");const t=["projectId","apiKey","appId"];for(const n of t)if(!e.options[n])throw C(n);return{appName:e.name,projectId:e.options.projectId,apiKey:e.options.apiKey,appId:e.options.appId}}function C(e){return h.create("missing-app-config-values",{valueName:e})}/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const me="installations",lt="installations-internal",gt=e=>{const t=e.getProvider("app").getImmediate(),n=pt(t),o=P(t,"heartbeat");return{app:t,appConfig:n,heartbeatServiceProvider:o,_delete:()=>Promise.resolve()}},wt=e=>{const t=e.getProvider("app").getImmediate(),n=P(t,me).getImmediate();return{getId:()=>ut(n),getToken:i=>dt(n,i)}};function ht(){k(new I(me,gt,"PUBLIC")),k(new I(lt,wt,"PRIVATE"))}ht();T(te,F);T(te,F,"esm2017");/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const bt="/firebase-messaging-sw.js",mt="/firebase-cloud-messaging-push-scope",ye="BDOU99-h67HcA6JeFXHbSNMu7e2yNNu3RzoMj8TM4W88jITfq7ZmPvIM1Iv-4_l2LxQcYwhqby2xGpWwzjfAnG4",yt="https://fcmregistrations.googleapis.com/v1",Te="google.c.a.c_id",Tt="google.c.a.c_l",kt="google.c.a.ts",It="google.c.a.e",G=1e4;var J;(function(e){e[e.DATA_MESSAGE=1]="DATA_MESSAGE",e[e.DISPLAY_NOTIFICATION=3]="DISPLAY_NOTIFICATION"})(J||(J={}));/**
 * @license
 * Copyright 2018 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software distributed under the License
 * is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the License for the specific language governing permissions and limitations under
 * the License.
 */var y;(function(e){e.PUSH_RECEIVED="push-received",e.NOTIFICATION_CLICKED="notification-clicked"})(y||(y={}));/**
 * @license
 * Copyright 2017 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function g(e){const t=new Uint8Array(e);return btoa(String.fromCharCode(...t)).replace(/=/g,"").replace(/\+/g,"-").replace(/\//g,"_")}function vt(e){const t="=".repeat((4-e.length%4)%4),n=(e+t).replace(/\-/g,"+").replace(/_/g,"/"),o=atob(n),i=new Uint8Array(o.length);for(let r=0;r<o.length;++r)i[r]=o.charCodeAt(r);return i}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const N="fcm_token_details_db",St=5,Y="fcm_token_object_Store";function At(e){return s(this,null,function*(){if("databases"in indexedDB&&!(yield indexedDB.databases()).map(r=>r.name).includes(N))return null;let t=null;return(yield j(N,St,{upgrade:(o,i,r,a)=>s(this,null,function*(){var u;if(i<2||!o.objectStoreNames.contains(Y))return;const d=a.objectStore(Y),p=yield d.index("fcmSenderId").get(e);if(yield d.clear(),!!p){if(i===2){const c=p;if(!c.auth||!c.p256dh||!c.endpoint)return;t={token:c.fcmToken,createTime:(u=c.createTime)!==null&&u!==void 0?u:Date.now(),subscriptionOptions:{auth:c.auth,p256dh:c.p256dh,endpoint:c.endpoint,swScope:c.swScope,vapidKey:typeof c.vapidKey=="string"?c.vapidKey:g(c.vapidKey)}}}else if(i===3){const c=p;t={token:c.fcmToken,createTime:c.createTime,subscriptionOptions:{auth:g(c.auth),p256dh:g(c.p256dh),endpoint:c.endpoint,swScope:c.swScope,vapidKey:g(c.vapidKey)}}}else if(i===4){const c=p;t={token:c.fcmToken,createTime:c.createTime,subscriptionOptions:{auth:g(c.auth),p256dh:g(c.p256dh),endpoint:c.endpoint,swScope:c.swScope,vapidKey:g(c.vapidKey)}}}}})})).close(),yield _(N),yield _("fcm_vapid_details_db"),yield _("undefined"),Et(t)?t:null})}function Et(e){if(!e||!e.subscriptionOptions)return!1;const{subscriptionOptions:t}=e;return typeof e.createTime=="number"&&e.createTime>0&&typeof e.token=="string"&&e.token.length>0&&typeof t.auth=="string"&&t.auth.length>0&&typeof t.p256dh=="string"&&t.p256dh.length>0&&typeof t.endpoint=="string"&&t.endpoint.length>0&&typeof t.swScope=="string"&&t.swScope.length>0&&typeof t.vapidKey=="string"&&t.vapidKey.length>0}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const _t="firebase-messaging-database",Ot=1,m="firebase-messaging-store";let D=null;function L(){return D||(D=j(_t,Ot,{upgrade:(e,t)=>{switch(t){case 0:e.createObjectStore(m)}}})),D}function ke(e){return s(this,null,function*(){const t=V(e),o=yield(yield L()).transaction(m).objectStore(m).get(t);if(o)return o;{const i=yield At(e.appConfig.senderId);if(i)return yield x(e,i),i}})}function x(e,t){return s(this,null,function*(){const n=V(e),i=(yield L()).transaction(m,"readwrite");return yield i.objectStore(m).put(t,n),yield i.done,t})}function Ct(e){return s(this,null,function*(){const t=V(e),o=(yield L()).transaction(m,"readwrite");yield o.objectStore(m).delete(t),yield o.done})}function V({appConfig:e}){return e.appId}/**
 * @license
 * Copyright 2017 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const Nt={"missing-app-config-values":'Missing App configuration value: "{$valueName}"',"only-available-in-window":"This method is available in a Window context.","only-available-in-sw":"This method is available in a service worker context.","permission-default":"The notification permission was not granted and dismissed instead.","permission-blocked":"The notification permission was not granted and blocked instead.","unsupported-browser":"This browser doesn't support the API's required to use the Firebase SDK.","indexed-db-unsupported":"This browser doesn't support indexedDb.open() (ex. Safari iFrame, Firefox Private Browsing, etc)","failed-service-worker-registration":"We are unable to register the default service worker. {$browserErrorMessage}","token-subscribe-failed":"A problem occurred while subscribing the user to FCM: {$errorInfo}","token-subscribe-no-token":"FCM returned no token when subscribing the user to push.","token-unsubscribe-failed":"A problem occurred while unsubscribing the user from FCM: {$errorInfo}","token-update-failed":"A problem occurred while updating the user from FCM: {$errorInfo}","token-update-no-token":"FCM returned no token when updating the user to push.","use-sw-after-get-token":"The useServiceWorker() method may only be called once and must be called before calling getToken() to ensure your service worker is used.","invalid-sw-registration":"The input to useServiceWorker() must be a ServiceWorkerRegistration.","invalid-bg-handler":"The input to setBackgroundMessageHandler() must be a function.","invalid-vapid-key":"The public VAPID key must be a string.","use-vapid-key-after-get-token":"The usePublicVapidKey() method may only be called once and must be called before calling getToken() to ensure your VAPID key is used."},f=new ee("messaging","Messaging",Nt);/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function Dt(e,t){return s(this,null,function*(){const n=yield H(e),o=ve(t),i={method:"POST",headers:n,body:JSON.stringify(o)};let r;try{r=yield(yield fetch(B(e.appConfig),i)).json()}catch(a){throw f.create("token-subscribe-failed",{errorInfo:a==null?void 0:a.toString()})}if(r.error){const a=r.error.message;throw f.create("token-subscribe-failed",{errorInfo:a})}if(!r.token)throw f.create("token-subscribe-no-token");return r.token})}function Rt(e,t){return s(this,null,function*(){const n=yield H(e),o=ve(t.subscriptionOptions),i={method:"PATCH",headers:n,body:JSON.stringify(o)};let r;try{r=yield(yield fetch(`${B(e.appConfig)}/${t.token}`,i)).json()}catch(a){throw f.create("token-update-failed",{errorInfo:a==null?void 0:a.toString()})}if(r.error){const a=r.error.message;throw f.create("token-update-failed",{errorInfo:a})}if(!r.token)throw f.create("token-update-no-token");return r.token})}function Ie(e,t){return s(this,null,function*(){const o={method:"DELETE",headers:yield H(e)};try{const r=yield(yield fetch(`${B(e.appConfig)}/${t}`,o)).json();if(r.error){const a=r.error.message;throw f.create("token-unsubscribe-failed",{errorInfo:a})}}catch(i){throw f.create("token-unsubscribe-failed",{errorInfo:i==null?void 0:i.toString()})}})}function B({projectId:e}){return`${yt}/projects/${e}/registrations`}function H(n){return s(this,arguments,function*({appConfig:e,installations:t}){const o=yield t.getToken();return new Headers({"Content-Type":"application/json",Accept:"application/json","x-goog-api-key":e.apiKey,"x-goog-firebase-installations-auth":`FIS ${o}`})})}function ve({p256dh:e,auth:t,endpoint:n,vapidKey:o}){const i={web:{endpoint:n,auth:t,p256dh:e}};return o!==ye&&(i.web.applicationPubKey=o),i}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const Mt=7*24*60*60*1e3;function Pt(e){return s(this,null,function*(){const t=yield $t(e.swRegistration,e.vapidKey),n={vapidKey:e.vapidKey,swScope:e.swRegistration.scope,endpoint:t.endpoint,auth:g(t.getKey("auth")),p256dh:g(t.getKey("p256dh"))},o=yield ke(e.firebaseDependencies);if(o){if(Kt(o.subscriptionOptions,n))return Date.now()>=o.createTime+Mt?Ft(e,{token:o.token,createTime:Date.now(),subscriptionOptions:n}):o.token;try{yield Ie(e.firebaseDependencies,o.token)}catch(i){console.warn(i)}return z(e.firebaseDependencies,n)}else return z(e.firebaseDependencies,n)})}function jt(e){return s(this,null,function*(){const t=yield ke(e.firebaseDependencies);t&&(yield Ie(e.firebaseDependencies,t.token),yield Ct(e.firebaseDependencies));const n=yield e.swRegistration.pushManager.getSubscription();return n?n.unsubscribe():!0})}function Ft(e,t){return s(this,null,function*(){try{const n=yield Rt(e.firebaseDependencies,t),o=Object.assign(Object.assign({},t),{token:n,createTime:Date.now()});return yield x(e.firebaseDependencies,o),n}catch(n){throw n}})}function z(e,t){return s(this,null,function*(){const o={token:yield Dt(e,t),createTime:Date.now(),subscriptionOptions:t};return yield x(e,o),o.token})}function $t(e,t){return s(this,null,function*(){const n=yield e.pushManager.getSubscription();return n||e.pushManager.subscribe({userVisibleOnly:!0,applicationServerKey:vt(t)})})}function Kt(e,t){const n=t.vapidKey===e.vapidKey,o=t.endpoint===e.endpoint,i=t.auth===e.auth,r=t.p256dh===e.p256dh;return n&&o&&i&&r}/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function X(e){const t={from:e.from,collapseKey:e.collapse_key,messageId:e.fcmMessageId};return qt(t,e),Lt(t,e),xt(t,e),t}function qt(e,t){if(!t.notification)return;e.notification={};const n=t.notification.title;n&&(e.notification.title=n);const o=t.notification.body;o&&(e.notification.body=o);const i=t.notification.image;i&&(e.notification.image=i);const r=t.notification.icon;r&&(e.notification.icon=r)}function Lt(e,t){t.data&&(e.data=t.data)}function xt(e,t){var n,o,i,r,a;if(!t.fcmOptions&&!(!((n=t.notification)===null||n===void 0)&&n.click_action))return;e.fcmOptions={};const u=(i=(o=t.fcmOptions)===null||o===void 0?void 0:o.link)!==null&&i!==void 0?i:(r=t.notification)===null||r===void 0?void 0:r.click_action;u&&(e.fcmOptions.link=u);const d=(a=t.fcmOptions)===null||a===void 0?void 0:a.analytics_label;d&&(e.fcmOptions.analyticsLabel=d)}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function Vt(e){return typeof e=="object"&&!!e&&Te in e}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function Bt(e){if(!e||!e.options)throw R("App Configuration Object");if(!e.name)throw R("App Name");const t=["projectId","apiKey","appId","messagingSenderId"],{options:n}=e;for(const o of t)if(!n[o])throw R(o);return{appName:e.name,projectId:n.projectId,apiKey:n.apiKey,appId:n.appId,senderId:n.messagingSenderId}}function R(e){return f.create("missing-app-config-values",{valueName:e})}/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */class Ht{constructor(t,n,o){this.deliveryMetricsExportedToBigQueryEnabled=!1,this.onBackgroundMessageHandler=null,this.onMessageHandler=null,this.logEvents=[],this.isLogServiceStarted=!1;const i=Bt(t);this.firebaseDependencies={app:t,appConfig:i,installations:n,analyticsProvider:o}}_delete(){return Promise.resolve()}}/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function Se(e){return s(this,null,function*(){try{e.swRegistration=yield navigator.serviceWorker.register(bt,{scope:mt}),e.swRegistration.update().catch(()=>{}),yield Wt(e.swRegistration)}catch(t){throw f.create("failed-service-worker-registration",{browserErrorMessage:t==null?void 0:t.message})}})}function Wt(e){return s(this,null,function*(){return new Promise((t,n)=>{const o=setTimeout(()=>n(new Error(`Service worker not registered after ${G} ms`)),G),i=e.installing||e.waiting;e.active?(clearTimeout(o),t()):i?i.onstatechange=r=>{var a;((a=r.target)===null||a===void 0?void 0:a.state)==="activated"&&(i.onstatechange=null,clearTimeout(o),t())}:(clearTimeout(o),n(new Error("No incoming service worker found.")))})})}/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function Ut(e,t){return s(this,null,function*(){if(!t&&!e.swRegistration&&(yield Se(e)),!(!t&&e.swRegistration)){if(!(t instanceof ServiceWorkerRegistration))throw f.create("invalid-sw-registration");e.swRegistration=t}})}/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function Gt(e,t){return s(this,null,function*(){t?e.vapidKey=t:e.vapidKey||(e.vapidKey=ye)})}/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function Ae(e,t){return s(this,null,function*(){if(!navigator)throw f.create("only-available-in-window");if(Notification.permission==="default"&&(yield Notification.requestPermission()),Notification.permission!=="granted")throw f.create("permission-blocked");return yield Gt(e,t==null?void 0:t.vapidKey),yield Ut(e,t==null?void 0:t.serviceWorkerRegistration),Pt(e)})}/**
 * @license
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function Jt(e,t,n){return s(this,null,function*(){const o=Yt(t);(yield e.firebaseDependencies.analyticsProvider.get()).logEvent(o,{message_id:n[Te],message_name:n[Tt],message_time:n[kt],message_device_time:Math.floor(Date.now()/1e3)})})}function Yt(e){switch(e){case y.NOTIFICATION_CLICKED:return"notification_open";case y.PUSH_RECEIVED:return"notification_foreground";default:throw new Error}}/**
 * @license
 * Copyright 2017 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function zt(e,t){return s(this,null,function*(){const n=t.data;if(!n.isFirebaseMessaging)return;e.onMessageHandler&&n.messageType===y.PUSH_RECEIVED&&(typeof e.onMessageHandler=="function"?e.onMessageHandler(X(n)):e.onMessageHandler.next(X(n)));const o=n.data;Vt(o)&&o[It]==="1"&&(yield Jt(e,n.messageType,o))})}const Q="@firebase/messaging",Z="0.12.22";/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const Xt=e=>{const t=new Ht(e.getProvider("app").getImmediate(),e.getProvider("installations-internal").getImmediate(),e.getProvider("analytics-internal"));return navigator.serviceWorker.addEventListener("message",n=>zt(t,n)),t},Qt=e=>{const t=e.getProvider("messaging").getImmediate();return{getToken:o=>Ae(t,o)}};function Zt(){k(new I("messaging",Xt,"PUBLIC")),k(new I("messaging-internal",Qt,"PRIVATE")),T(Q,Z),T(Q,Z,"esm2017")}/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function en(){return s(this,null,function*(){try{yield Ce()}catch(e){return!1}return typeof window!="undefined"&&Ne()&&De()&&"serviceWorker"in navigator&&"PushManager"in window&&"Notification"in window&&"fetch"in window&&ServiceWorkerRegistration.prototype.hasOwnProperty("showNotification")&&PushSubscription.prototype.hasOwnProperty("getKey")})}/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function tn(e){return s(this,null,function*(){if(!navigator)throw f.create("only-available-in-window");return e.swRegistration||(yield Se(e)),jt(e)})}/**
 * @license
 * Copyright 2020 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function nn(e,t){if(!navigator)throw f.create("only-available-in-window");return e.onMessageHandler=t,()=>{e.onMessageHandler=null}}/**
 * @license
 * Copyright 2017 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function an(e=Oe()){return en().then(t=>{if(!t)throw f.create("unsupported-browser")},t=>{throw f.create("indexed-db-unsupported")}),P(S(e),"messaging").getImmediate()}function sn(e,t){return s(this,null,function*(){return e=S(e),Ae(e,t)})}function cn(e){return e=S(e),tn(e)}function un(e,t){return e=S(e),nn(e,t)}Zt();export{cn as deleteToken,an as getMessaging,sn as getToken,en as isSupported,un as onMessage};
