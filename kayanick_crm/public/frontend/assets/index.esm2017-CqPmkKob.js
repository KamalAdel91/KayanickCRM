var me=Object.defineProperty,ge=Object.defineProperties;var be=Object.getOwnPropertyDescriptors;var k=Object.getOwnPropertySymbols;var _e=Object.prototype.hasOwnProperty,ye=Object.prototype.propertyIsEnumerable;var z=(t,e,n)=>e in t?me(t,e,{enumerable:!0,configurable:!0,writable:!0,value:n}):t[e]=n,j=(t,e)=>{for(var n in e||(e={}))_e.call(e,n)&&z(t,n,e[n]);if(k)for(var n of k(e))ye.call(e,n)&&z(t,n,e[n]);return t},V=(t,e)=>ge(t,be(e));var h=(t,e,n)=>new Promise((r,s)=>{var i=o=>{try{c(n.next(o))}catch(d){s(d)}},a=o=>{try{c(n.throw(o))}catch(d){s(d)}},c=o=>o.done?r(o.value):Promise.resolve(o.value).then(i,a);c((n=n.apply(t,e)).next())});const Ee=()=>{};var U={};/**
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
 */const ee=function(t){const e=[];let n=0;for(let r=0;r<t.length;r++){let s=t.charCodeAt(r);s<128?e[n++]=s:s<2048?(e[n++]=s>>6|192,e[n++]=s&63|128):(s&64512)===55296&&r+1<t.length&&(t.charCodeAt(r+1)&64512)===56320?(s=65536+((s&1023)<<10)+(t.charCodeAt(++r)&1023),e[n++]=s>>18|240,e[n++]=s>>12&63|128,e[n++]=s>>6&63|128,e[n++]=s&63|128):(e[n++]=s>>12|224,e[n++]=s>>6&63|128,e[n++]=s&63|128)}return e},ve=function(t){const e=[];let n=0,r=0;for(;n<t.length;){const s=t[n++];if(s<128)e[r++]=String.fromCharCode(s);else if(s>191&&s<224){const i=t[n++];e[r++]=String.fromCharCode((s&31)<<6|i&63)}else if(s>239&&s<365){const i=t[n++],a=t[n++],c=t[n++],o=((s&7)<<18|(i&63)<<12|(a&63)<<6|c&63)-65536;e[r++]=String.fromCharCode(55296+(o>>10)),e[r++]=String.fromCharCode(56320+(o&1023))}else{const i=t[n++],a=t[n++];e[r++]=String.fromCharCode((s&15)<<12|(i&63)<<6|a&63)}}return e.join("")},te={byteToCharMap_:null,charToByteMap_:null,byteToCharMapWebSafe_:null,charToByteMapWebSafe_:null,ENCODED_VALS_BASE:"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",get ENCODED_VALS(){return this.ENCODED_VALS_BASE+"+/="},get ENCODED_VALS_WEBSAFE(){return this.ENCODED_VALS_BASE+"-_."},HAS_NATIVE_SUPPORT:typeof atob=="function",encodeByteArray(t,e){if(!Array.isArray(t))throw Error("encodeByteArray takes an array as a parameter");this.init_();const n=e?this.byteToCharMapWebSafe_:this.byteToCharMap_,r=[];for(let s=0;s<t.length;s+=3){const i=t[s],a=s+1<t.length,c=a?t[s+1]:0,o=s+2<t.length,d=o?t[s+2]:0,D=i>>2,m=(i&3)<<4|c>>4;let I=(c&15)<<2|d>>6,C=d&63;o||(C=64,a||(I=64)),r.push(n[D],n[m],n[I],n[C])}return r.join("")},encodeString(t,e){return this.HAS_NATIVE_SUPPORT&&!e?btoa(t):this.encodeByteArray(ee(t),e)},decodeString(t,e){return this.HAS_NATIVE_SUPPORT&&!e?atob(t):ve(this.decodeStringToByteArray(t,e))},decodeStringToByteArray(t,e){this.init_();const n=e?this.charToByteMapWebSafe_:this.charToByteMap_,r=[];for(let s=0;s<t.length;){const i=n[t.charAt(s++)],c=s<t.length?n[t.charAt(s)]:0;++s;const d=s<t.length?n[t.charAt(s)]:64;++s;const m=s<t.length?n[t.charAt(s)]:64;if(++s,i==null||c==null||d==null||m==null)throw new De;const I=i<<2|c>>4;if(r.push(I),d!==64){const C=c<<4&240|d>>2;if(r.push(C),m!==64){const pe=d<<6&192|m;r.push(pe)}}}return r},init_(){if(!this.byteToCharMap_){this.byteToCharMap_={},this.charToByteMap_={},this.byteToCharMapWebSafe_={},this.charToByteMapWebSafe_={};for(let t=0;t<this.ENCODED_VALS.length;t++)this.byteToCharMap_[t]=this.ENCODED_VALS.charAt(t),this.charToByteMap_[this.byteToCharMap_[t]]=t,this.byteToCharMapWebSafe_[t]=this.ENCODED_VALS_WEBSAFE.charAt(t),this.charToByteMapWebSafe_[this.byteToCharMapWebSafe_[t]]=t,t>=this.ENCODED_VALS_BASE.length&&(this.charToByteMap_[this.ENCODED_VALS_WEBSAFE.charAt(t)]=t,this.charToByteMapWebSafe_[this.ENCODED_VALS.charAt(t)]=t)}}};class De extends Error{constructor(){super(...arguments),this.name="DecodeBase64StringError"}}const Ie=function(t){const e=ee(t);return te.encodeByteArray(e,!0)},ne=function(t){return Ie(t).replace(/\./g,"")},re=function(t){try{return te.decodeString(t,!0)}catch(e){console.error("base64Decode failed: ",e)}return null};/**
 * @license
 * Copyright 2022 Google LLC
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
 */function Ce(){if(typeof self!="undefined")return self;if(typeof window!="undefined")return window;if(typeof global!="undefined")return global;throw new Error("Unable to locate global object.")}/**
 * @license
 * Copyright 2022 Google LLC
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
 */const Se=()=>Ce().__FIREBASE_DEFAULTS__,we=()=>{if(typeof process=="undefined"||typeof U=="undefined")return;const t=U.__FIREBASE_DEFAULTS__;if(t)return JSON.parse(t)},Ae=()=>{if(typeof document=="undefined")return;let t;try{t=document.cookie.match(/__FIREBASE_DEFAULTS__=([^;]+)/)}catch(n){return}const e=t&&re(t[1]);return e&&JSON.parse(e)},Be=()=>{try{return Ee()||Se()||we()||Ae()}catch(t){console.info(`Unable to get __FIREBASE_DEFAULTS__ due to: ${t}`);return}},se=()=>{var t;return(t=Be())===null||t===void 0?void 0:t.config};/**
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
 */class Oe{constructor(){this.reject=()=>{},this.resolve=()=>{},this.promise=new Promise((e,n)=>{this.resolve=e,this.reject=n})}wrapCallback(e){return(n,r)=>{n?this.reject(n):this.resolve(r),typeof e=="function"&&(this.promise.catch(()=>{}),e.length===1?e(n):e(n,r))}}}function Te(){return typeof window!="undefined"||ie()}function ie(){return typeof WorkerGlobalScope!="undefined"&&typeof self!="undefined"&&self instanceof WorkerGlobalScope}function Re(){try{return typeof indexedDB=="object"}catch(t){return!1}}function Me(){return new Promise((t,e)=>{try{let n=!0;const r="validate-browser-context-for-indexeddb-analytics-module",s=self.indexedDB.open(r);s.onsuccess=()=>{s.result.close(),n||self.indexedDB.deleteDatabase(r),t(!0)},s.onupgradeneeded=()=>{n=!1},s.onerror=()=>{var i;e(((i=s.error)===null||i===void 0?void 0:i.message)||"")}}catch(n){e(n)}})}function Yt(){return!(typeof navigator=="undefined"||!navigator.cookieEnabled)}/**
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
 */const $e="FirebaseError";class v extends Error{constructor(e,n,r){super(n),this.code=e,this.customData=r,this.name=$e,Object.setPrototypeOf(this,v.prototype),Error.captureStackTrace&&Error.captureStackTrace(this,ae.prototype.create)}}class ae{constructor(e,n,r){this.service=e,this.serviceName=n,this.errors=r}create(e,...n){const r=n[0]||{},s=`${this.service}/${e}`,i=this.errors[e],a=i?Ne(i,r):"Error",c=`${this.serviceName}: ${a} (${s}).`;return new v(s,c,r)}}function Ne(t,e){return t.replace(Le,(n,r)=>{const s=e[r];return s!=null?String(s):`<${r}?>`})}const Le=/\{\$([^}]+)}/g;function $(t,e){if(t===e)return!0;const n=Object.keys(t),r=Object.keys(e);for(const s of n){if(!r.includes(s))return!1;const i=t[s],a=e[s];if(W(i)&&W(a)){if(!$(i,a))return!1}else if(i!==a)return!1}for(const s of r)if(!n.includes(s))return!1;return!0}function W(t){return t!==null&&typeof t=="object"}/**
 * @license
 * Copyright 2021 Google LLC
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
 */function Xt(t){return t&&t._delegate?t._delegate:t}class w{constructor(e,n,r){this.name=e,this.instanceFactory=n,this.type=r,this.multipleInstances=!1,this.serviceProps={},this.instantiationMode="LAZY",this.onInstanceCreated=null}setInstantiationMode(e){return this.instantiationMode=e,this}setMultipleInstances(e){return this.multipleInstances=e,this}setServiceProps(e){return this.serviceProps=e,this}setInstanceCreatedCallback(e){return this.onInstanceCreated=e,this}}/**
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
 */const g="[DEFAULT]";/**
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
 */class Fe{constructor(e,n){this.name=e,this.container=n,this.component=null,this.instances=new Map,this.instancesDeferred=new Map,this.instancesOptions=new Map,this.onInitCallbacks=new Map}get(e){const n=this.normalizeInstanceIdentifier(e);if(!this.instancesDeferred.has(n)){const r=new Oe;if(this.instancesDeferred.set(n,r),this.isInitialized(n)||this.shouldAutoInitialize())try{const s=this.getOrInitializeService({instanceIdentifier:n});s&&r.resolve(s)}catch(s){}}return this.instancesDeferred.get(n).promise}getImmediate(e){var n;const r=this.normalizeInstanceIdentifier(e==null?void 0:e.identifier),s=(n=e==null?void 0:e.optional)!==null&&n!==void 0?n:!1;if(this.isInitialized(r)||this.shouldAutoInitialize())try{return this.getOrInitializeService({instanceIdentifier:r})}catch(i){if(s)return null;throw i}else{if(s)return null;throw Error(`Service ${this.name} is not available`)}}getComponent(){return this.component}setComponent(e){if(e.name!==this.name)throw Error(`Mismatching Component ${e.name} for Provider ${this.name}.`);if(this.component)throw Error(`Component for ${this.name} has already been provided`);if(this.component=e,!!this.shouldAutoInitialize()){if(Pe(e))try{this.getOrInitializeService({instanceIdentifier:g})}catch(n){}for(const[n,r]of this.instancesDeferred.entries()){const s=this.normalizeInstanceIdentifier(n);try{const i=this.getOrInitializeService({instanceIdentifier:s});r.resolve(i)}catch(i){}}}}clearInstance(e=g){this.instancesDeferred.delete(e),this.instancesOptions.delete(e),this.instances.delete(e)}delete(){return h(this,null,function*(){const e=Array.from(this.instances.values());yield Promise.all([...e.filter(n=>"INTERNAL"in n).map(n=>n.INTERNAL.delete()),...e.filter(n=>"_delete"in n).map(n=>n._delete())])})}isComponentSet(){return this.component!=null}isInitialized(e=g){return this.instances.has(e)}getOptions(e=g){return this.instancesOptions.get(e)||{}}initialize(e={}){const{options:n={}}=e,r=this.normalizeInstanceIdentifier(e.instanceIdentifier);if(this.isInitialized(r))throw Error(`${this.name}(${r}) has already been initialized`);if(!this.isComponentSet())throw Error(`Component ${this.name} has not been registered yet`);const s=this.getOrInitializeService({instanceIdentifier:r,options:n});for(const[i,a]of this.instancesDeferred.entries()){const c=this.normalizeInstanceIdentifier(i);r===c&&a.resolve(s)}return s}onInit(e,n){var r;const s=this.normalizeInstanceIdentifier(n),i=(r=this.onInitCallbacks.get(s))!==null&&r!==void 0?r:new Set;i.add(e),this.onInitCallbacks.set(s,i);const a=this.instances.get(s);return a&&e(a,s),()=>{i.delete(e)}}invokeOnInitCallbacks(e,n){const r=this.onInitCallbacks.get(n);if(r)for(const s of r)try{s(e,n)}catch(i){}}getOrInitializeService({instanceIdentifier:e,options:n={}}){let r=this.instances.get(e);if(!r&&this.component&&(r=this.component.instanceFactory(this.container,{instanceIdentifier:He(e),options:n}),this.instances.set(e,r),this.instancesOptions.set(e,n),this.invokeOnInitCallbacks(r,e),this.component.onInstanceCreated))try{this.component.onInstanceCreated(this.container,e,r)}catch(s){}return r||null}normalizeInstanceIdentifier(e=g){return this.component?this.component.multipleInstances?e:g:e}shouldAutoInitialize(){return!!this.component&&this.component.instantiationMode!=="EXPLICIT"}}function He(t){return t===g?void 0:t}function Pe(t){return t.instantiationMode==="EAGER"}/**
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
 */class oe{constructor(e){this.name=e,this.providers=new Map}addComponent(e){const n=this.getProvider(e.name);if(n.isComponentSet())throw new Error(`Component ${e.name} has already been registered with ${this.name}`);n.setComponent(e)}addOrOverwriteComponent(e){this.getProvider(e.name).isComponentSet()&&this.providers.delete(e.name),this.addComponent(e)}getProvider(e){if(this.providers.has(e))return this.providers.get(e);const n=new Fe(e,this);return this.providers.set(e,n),n}getProviders(){return Array.from(this.providers.values())}}/**
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
 */const P=[];var l;(function(t){t[t.DEBUG=0]="DEBUG",t[t.VERBOSE=1]="VERBOSE",t[t.INFO=2]="INFO",t[t.WARN=3]="WARN",t[t.ERROR=4]="ERROR",t[t.SILENT=5]="SILENT"})(l||(l={}));const ce={debug:l.DEBUG,verbose:l.VERBOSE,info:l.INFO,warn:l.WARN,error:l.ERROR,silent:l.SILENT},xe=l.INFO,ke={[l.DEBUG]:"log",[l.VERBOSE]:"log",[l.INFO]:"info",[l.WARN]:"warn",[l.ERROR]:"error"},ze=(t,e,...n)=>{if(e<t.logLevel)return;const r=new Date().toISOString(),s=ke[e];if(s)console[s](`[${r}]  ${t.name}:`,...n);else throw new Error(`Attempted to log a message with an invalid logType (value: ${e})`)};class je{constructor(e){this.name=e,this._logLevel=xe,this._logHandler=ze,this._userLogHandler=null,P.push(this)}get logLevel(){return this._logLevel}set logLevel(e){if(!(e in l))throw new TypeError(`Invalid value "${e}" assigned to \`logLevel\``);this._logLevel=e}setLogLevel(e){this._logLevel=typeof e=="string"?ce[e]:e}get logHandler(){return this._logHandler}set logHandler(e){if(typeof e!="function")throw new TypeError("Value assigned to `logHandler` must be a function");this._logHandler=e}get userLogHandler(){return this._userLogHandler}set userLogHandler(e){this._userLogHandler=e}debug(...e){this._userLogHandler&&this._userLogHandler(this,l.DEBUG,...e),this._logHandler(this,l.DEBUG,...e)}log(...e){this._userLogHandler&&this._userLogHandler(this,l.VERBOSE,...e),this._logHandler(this,l.VERBOSE,...e)}info(...e){this._userLogHandler&&this._userLogHandler(this,l.INFO,...e),this._logHandler(this,l.INFO,...e)}warn(...e){this._userLogHandler&&this._userLogHandler(this,l.WARN,...e),this._logHandler(this,l.WARN,...e)}error(...e){this._userLogHandler&&this._userLogHandler(this,l.ERROR,...e),this._logHandler(this,l.ERROR,...e)}}function Ve(t){P.forEach(e=>{e.setLogLevel(t)})}function Ue(t,e){for(const n of P){let r=null;e&&e.level&&(r=ce[e.level]),t===null?n.userLogHandler=null:n.userLogHandler=(s,i,...a)=>{const c=a.map(o=>{if(o==null)return null;if(typeof o=="string")return o;if(typeof o=="number"||typeof o=="boolean")return o.toString();if(o instanceof Error)return o.message;try{return JSON.stringify(o)}catch(d){return null}}).filter(o=>o).join(" ");i>=(r!=null?r:s.logLevel)&&t({level:l[i].toLowerCase(),message:c,args:a,type:s.name})}}}const We=(t,e)=>e.some(n=>t instanceof n);let G,J;function Ge(){return G||(G=[IDBDatabase,IDBObjectStore,IDBIndex,IDBCursor,IDBTransaction])}function Je(){return J||(J=[IDBCursor.prototype.advance,IDBCursor.prototype.continue,IDBCursor.prototype.continuePrimaryKey])}const le=new WeakMap,N=new WeakMap,de=new WeakMap,O=new WeakMap,x=new WeakMap;function Ke(t){const e=new Promise((n,r)=>{const s=()=>{t.removeEventListener("success",i),t.removeEventListener("error",a)},i=()=>{n(u(t.result)),s()},a=()=>{r(t.error),s()};t.addEventListener("success",i),t.addEventListener("error",a)});return e.then(n=>{n instanceof IDBCursor&&le.set(n,t)}).catch(()=>{}),x.set(e,t),e}function Ye(t){if(N.has(t))return;const e=new Promise((n,r)=>{const s=()=>{t.removeEventListener("complete",i),t.removeEventListener("error",a),t.removeEventListener("abort",a)},i=()=>{n(),s()},a=()=>{r(t.error||new DOMException("AbortError","AbortError")),s()};t.addEventListener("complete",i),t.addEventListener("error",a),t.addEventListener("abort",a)});N.set(t,e)}let L={get(t,e,n){if(t instanceof IDBTransaction){if(e==="done")return N.get(t);if(e==="objectStoreNames")return t.objectStoreNames||de.get(t);if(e==="store")return n.objectStoreNames[1]?void 0:n.objectStore(n.objectStoreNames[0])}return u(t[e])},set(t,e,n){return t[e]=n,!0},has(t,e){return t instanceof IDBTransaction&&(e==="done"||e==="store")?!0:e in t}};function Xe(t){L=t(L)}function qe(t){return t===IDBDatabase.prototype.transaction&&!("objectStoreNames"in IDBTransaction.prototype)?function(e,...n){const r=t.call(T(this),e,...n);return de.set(r,e.sort?e.sort():[e]),u(r)}:Je().includes(t)?function(...e){return t.apply(T(this),e),u(le.get(this))}:function(...e){return u(t.apply(T(this),e))}}function Ze(t){return typeof t=="function"?qe(t):(t instanceof IDBTransaction&&Ye(t),We(t,Ge())?new Proxy(t,L):t)}function u(t){if(t instanceof IDBRequest)return Ke(t);if(O.has(t))return O.get(t);const e=Ze(t);return e!==t&&(O.set(t,e),x.set(e,t)),e}const T=t=>x.get(t);function Qe(t,e,{blocked:n,upgrade:r,blocking:s,terminated:i}={}){const a=indexedDB.open(t,e),c=u(a);return r&&a.addEventListener("upgradeneeded",o=>{r(u(a.result),o.oldVersion,o.newVersion,u(a.transaction),o)}),n&&a.addEventListener("blocked",o=>n(o.oldVersion,o.newVersion,o)),c.then(o=>{i&&o.addEventListener("close",()=>i()),s&&o.addEventListener("versionchange",d=>s(d.oldVersion,d.newVersion,d))}).catch(()=>{}),c}function qt(t,{blocked:e}={}){const n=indexedDB.deleteDatabase(t);return e&&n.addEventListener("blocked",r=>e(r.oldVersion,r)),u(n).then(()=>{})}const et=["get","getKey","getAll","getAllKeys","count"],tt=["put","add","delete","clear"],R=new Map;function K(t,e){if(!(t instanceof IDBDatabase&&!(e in t)&&typeof e=="string"))return;if(R.get(e))return R.get(e);const n=e.replace(/FromIndex$/,""),r=e!==n,s=tt.includes(n);if(!(n in(r?IDBIndex:IDBObjectStore).prototype)||!(s||et.includes(n)))return;const i=function(a,...c){return h(this,null,function*(){const o=this.transaction(a,s?"readwrite":"readonly");let d=o.store;return r&&(d=d.index(c.shift())),(yield Promise.all([d[n](...c),s&&o.done]))[0]})};return R.set(e,i),i}Xe(t=>V(j({},t),{get:(e,n,r)=>K(e,n)||t.get(e,n,r),has:(e,n)=>!!K(e,n)||t.has(e,n)}));/**
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
 */class nt{constructor(e){this.container=e}getPlatformInfoString(){return this.container.getProviders().map(n=>{if(rt(n)){const r=n.getImmediate();return`${r.library}/${r.version}`}else return null}).filter(n=>n).join(" ")}}function rt(t){const e=t.getComponent();return(e==null?void 0:e.type)==="VERSION"}const A="@firebase/app",F="0.13.2";/**
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
 */const p=new je("@firebase/app"),st="@firebase/app-compat",it="@firebase/analytics-compat",at="@firebase/analytics",ot="@firebase/app-check-compat",ct="@firebase/app-check",lt="@firebase/auth",dt="@firebase/auth-compat",ht="@firebase/database",ft="@firebase/data-connect",ut="@firebase/database-compat",pt="@firebase/functions",mt="@firebase/functions-compat",gt="@firebase/installations",bt="@firebase/installations-compat",_t="@firebase/messaging",yt="@firebase/messaging-compat",Et="@firebase/performance",vt="@firebase/performance-compat",Dt="@firebase/remote-config",It="@firebase/remote-config-compat",Ct="@firebase/storage",St="@firebase/storage-compat",wt="@firebase/firestore",At="@firebase/ai",Bt="@firebase/firestore-compat",Ot="firebase",Tt="11.10.0";/**
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
 */const B="[DEFAULT]",Rt={[A]:"fire-core",[st]:"fire-core-compat",[at]:"fire-analytics",[it]:"fire-analytics-compat",[ct]:"fire-app-check",[ot]:"fire-app-check-compat",[lt]:"fire-auth",[dt]:"fire-auth-compat",[ht]:"fire-rtdb",[ft]:"fire-data-connect",[ut]:"fire-rtdb-compat",[pt]:"fire-fn",[mt]:"fire-fn-compat",[gt]:"fire-iid",[bt]:"fire-iid-compat",[_t]:"fire-fcm",[yt]:"fire-fcm-compat",[Et]:"fire-perf",[vt]:"fire-perf-compat",[Dt]:"fire-rc",[It]:"fire-rc-compat",[Ct]:"fire-gcs",[St]:"fire-gcs-compat",[wt]:"fire-fst",[Bt]:"fire-fst-compat",[At]:"fire-vertex","fire-js":"fire-js",[Ot]:"fire-js-all"};/**
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
 */const b=new Map,_=new Map,y=new Map;function Y(t,e){try{t.container.addComponent(e)}catch(n){p.debug(`Component ${e.name} failed to register with FirebaseApp ${t.name}`,n)}}function Zt(t,e){t.container.addOrOverwriteComponent(e)}function H(t){const e=t.name;if(y.has(e))return p.debug(`There were multiple attempts to register component ${e}.`),!1;y.set(e,t);for(const n of b.values())Y(n,t);for(const n of _.values())Y(n,t);return!0}function Mt(t,e){const n=t.container.getProvider("heartbeat").getImmediate({optional:!0});return n&&n.triggerHeartbeat(),t.container.getProvider(e)}function Qt(t,e,n=B){Mt(t,e).clearInstance(n)}function $t(t){return t.options!==void 0}function en(t){return t==null?!1:t.settings!==void 0}function tn(){y.clear()}/**
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
 */const Nt={"no-app":"No Firebase App '{$appName}' has been created - call initializeApp() first","bad-app-name":"Illegal App name: '{$appName}'","duplicate-app":"Firebase App named '{$appName}' already exists with different options or config","app-deleted":"Firebase App named '{$appName}' already deleted","server-app-deleted":"Firebase Server App has been deleted","no-options":"Need to provide options, when not being deployed to hosting via source.","invalid-app-argument":"firebase.{$appName}() takes either no argument or a Firebase App instance.","invalid-log-argument":"First argument to `onLog` must be null or a function.","idb-open":"Error thrown when opening IndexedDB. Original error: {$originalErrorMessage}.","idb-get":"Error thrown when reading from IndexedDB. Original error: {$originalErrorMessage}.","idb-set":"Error thrown when writing to IndexedDB. Original error: {$originalErrorMessage}.","idb-delete":"Error thrown when deleting from IndexedDB. Original error: {$originalErrorMessage}.","finalization-registry-not-supported":"FirebaseServerApp deleteOnDeref field defined but the JS runtime does not support FinalizationRegistry.","invalid-server-app-environment":"FirebaseServerApp is not for use in browser environments."},f=new ae("app","Firebase",Nt);/**
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
 */class he{constructor(e,n,r){this._isDeleted=!1,this._options=Object.assign({},e),this._config=Object.assign({},n),this._name=n.name,this._automaticDataCollectionEnabled=n.automaticDataCollectionEnabled,this._container=r,this.container.addComponent(new w("app",()=>this,"PUBLIC"))}get automaticDataCollectionEnabled(){return this.checkDestroyed(),this._automaticDataCollectionEnabled}set automaticDataCollectionEnabled(e){this.checkDestroyed(),this._automaticDataCollectionEnabled=e}get name(){return this.checkDestroyed(),this._name}get options(){return this.checkDestroyed(),this._options}get config(){return this.checkDestroyed(),this._config}get container(){return this._container}get isDeleted(){return this._isDeleted}set isDeleted(e){this._isDeleted=e}checkDestroyed(){if(this.isDeleted)throw f.create("app-deleted",{appName:this._name})}}/**
 * @license
 * Copyright 2023 Google LLC
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
 */function X(t,e){const n=re(t.split(".")[1]);if(n===null){console.error(`FirebaseServerApp ${e} is invalid: second part could not be parsed.`);return}if(JSON.parse(n).exp===void 0){console.error(`FirebaseServerApp ${e} is invalid: expiration claim could not be parsed`);return}const s=JSON.parse(n).exp*1e3,i=new Date().getTime();s-i<=0&&console.error(`FirebaseServerApp ${e} is invalid: the token has expired.`)}class Lt extends he{constructor(e,n,r,s){const i=n.automaticDataCollectionEnabled!==void 0?n.automaticDataCollectionEnabled:!0,a={name:r,automaticDataCollectionEnabled:i};if(e.apiKey!==void 0)super(e,a,s);else{const c=e;super(c.options,a,s)}this._serverConfig=Object.assign({automaticDataCollectionEnabled:i},n),this._serverConfig.authIdToken&&X(this._serverConfig.authIdToken,"authIdToken"),this._serverConfig.appCheckToken&&X(this._serverConfig.appCheckToken,"appCheckToken"),this._finalizationRegistry=null,typeof FinalizationRegistry!="undefined"&&(this._finalizationRegistry=new FinalizationRegistry(()=>{this.automaticCleanup()})),this._refCount=0,this.incRefCount(this._serverConfig.releaseOnDeref),this._serverConfig.releaseOnDeref=void 0,n.releaseOnDeref=void 0,S(A,F,"serverapp")}toJSON(){}get refCount(){return this._refCount}incRefCount(e){this.isDeleted||(this._refCount++,e!==void 0&&this._finalizationRegistry!==null&&this._finalizationRegistry.register(e,this))}decRefCount(){return this.isDeleted?0:--this._refCount}automaticCleanup(){Ht(this)}get settings(){return this.checkDestroyed(),this._serverConfig}checkDestroyed(){if(this.isDeleted)throw f.create("server-app-deleted")}}/**
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
 */const nn=Tt;function Ft(t,e={}){let n=t;typeof e!="object"&&(e={name:e});const r=Object.assign({name:B,automaticDataCollectionEnabled:!0},e),s=r.name;if(typeof s!="string"||!s)throw f.create("bad-app-name",{appName:String(s)});if(n||(n=se()),!n)throw f.create("no-options");const i=b.get(s);if(i){if($(n,i.options)&&$(r,i.config))return i;throw f.create("duplicate-app",{appName:s})}const a=new oe(s);for(const o of y.values())a.addComponent(o);const c=new he(n,r,a);return b.set(s,c),c}function rn(t,e){if(Te()&&!ie())throw f.create("invalid-server-app-environment");e.automaticDataCollectionEnabled===void 0&&(e.automaticDataCollectionEnabled=!0);let n;$t(t)?n=t.options:n=t;const r=Object.assign(Object.assign({},e),n);r.releaseOnDeref!==void 0&&delete r.releaseOnDeref;const s=d=>[...d].reduce((D,m)=>Math.imul(31,D)+m.charCodeAt(0)|0,0);if(e.releaseOnDeref!==void 0&&typeof FinalizationRegistry=="undefined")throw f.create("finalization-registry-not-supported",{});const i=""+s(JSON.stringify(r)),a=_.get(i);if(a)return a.incRefCount(e.releaseOnDeref),a;const c=new oe(i);for(const d of y.values())c.addComponent(d);const o=new Lt(n,e,i,c);return _.set(i,o),o}function sn(t=B){const e=b.get(t);if(!e&&t===B&&se())return Ft();if(!e)throw f.create("no-app",{appName:t});return e}function an(){return Array.from(b.values())}function Ht(t){return h(this,null,function*(){let e=!1;const n=t.name;b.has(n)?(e=!0,b.delete(n)):_.has(n)&&t.decRefCount()<=0&&(_.delete(n),e=!0),e&&(yield Promise.all(t.container.getProviders().map(r=>r.delete())),t.isDeleted=!0)})}function S(t,e,n){var r;let s=(r=Rt[t])!==null&&r!==void 0?r:t;n&&(s+=`-${n}`);const i=s.match(/\s|\//),a=e.match(/\s|\//);if(i||a){const c=[`Unable to register library "${s}" with version "${e}":`];i&&c.push(`library name "${s}" contains illegal characters (whitespace or "/")`),i&&a&&c.push("and"),a&&c.push(`version name "${e}" contains illegal characters (whitespace or "/")`),p.warn(c.join(" "));return}H(new w(`${s}-version`,()=>({library:s,version:e}),"VERSION"))}function on(t,e){if(t!==null&&typeof t!="function")throw f.create("invalid-log-argument");Ue(t,e)}function cn(t){Ve(t)}/**
 * @license
 * Copyright 2021 Google LLC
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
 */const Pt="firebase-heartbeat-database",xt=1,E="firebase-heartbeat-store";let M=null;function fe(){return M||(M=Qe(Pt,xt,{upgrade:(t,e)=>{switch(e){case 0:try{t.createObjectStore(E)}catch(n){console.warn(n)}}}}).catch(t=>{throw f.create("idb-open",{originalErrorMessage:t.message})})),M}function kt(t){return h(this,null,function*(){try{const n=(yield fe()).transaction(E),r=yield n.objectStore(E).get(ue(t));return yield n.done,r}catch(e){if(e instanceof v)p.warn(e.message);else{const n=f.create("idb-get",{originalErrorMessage:e==null?void 0:e.message});p.warn(n.message)}}})}function q(t,e){return h(this,null,function*(){try{const r=(yield fe()).transaction(E,"readwrite");yield r.objectStore(E).put(e,ue(t)),yield r.done}catch(n){if(n instanceof v)p.warn(n.message);else{const r=f.create("idb-set",{originalErrorMessage:n==null?void 0:n.message});p.warn(r.message)}}})}function ue(t){return`${t.name}!${t.options.appId}`}/**
 * @license
 * Copyright 2021 Google LLC
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
 */const zt=1024,jt=30;class Vt{constructor(e){this.container=e,this._heartbeatsCache=null;const n=this.container.getProvider("app").getImmediate();this._storage=new Wt(n),this._heartbeatsCachePromise=this._storage.read().then(r=>(this._heartbeatsCache=r,r))}triggerHeartbeat(){return h(this,null,function*(){var e,n;try{const s=this.container.getProvider("platform-logger").getImmediate().getPlatformInfoString(),i=Z();if(((e=this._heartbeatsCache)===null||e===void 0?void 0:e.heartbeats)==null&&(this._heartbeatsCache=yield this._heartbeatsCachePromise,((n=this._heartbeatsCache)===null||n===void 0?void 0:n.heartbeats)==null)||this._heartbeatsCache.lastSentHeartbeatDate===i||this._heartbeatsCache.heartbeats.some(a=>a.date===i))return;if(this._heartbeatsCache.heartbeats.push({date:i,agent:s}),this._heartbeatsCache.heartbeats.length>jt){const a=Gt(this._heartbeatsCache.heartbeats);this._heartbeatsCache.heartbeats.splice(a,1)}return this._storage.overwrite(this._heartbeatsCache)}catch(r){p.warn(r)}})}getHeartbeatsHeader(){return h(this,null,function*(){var e;try{if(this._heartbeatsCache===null&&(yield this._heartbeatsCachePromise),((e=this._heartbeatsCache)===null||e===void 0?void 0:e.heartbeats)==null||this._heartbeatsCache.heartbeats.length===0)return"";const n=Z(),{heartbeatsToSend:r,unsentEntries:s}=Ut(this._heartbeatsCache.heartbeats),i=ne(JSON.stringify({version:2,heartbeats:r}));return this._heartbeatsCache.lastSentHeartbeatDate=n,s.length>0?(this._heartbeatsCache.heartbeats=s,yield this._storage.overwrite(this._heartbeatsCache)):(this._heartbeatsCache.heartbeats=[],this._storage.overwrite(this._heartbeatsCache)),i}catch(n){return p.warn(n),""}})}}function Z(){return new Date().toISOString().substring(0,10)}function Ut(t,e=zt){const n=[];let r=t.slice();for(const s of t){const i=n.find(a=>a.agent===s.agent);if(i){if(i.dates.push(s.date),Q(n)>e){i.dates.pop();break}}else if(n.push({agent:s.agent,dates:[s.date]}),Q(n)>e){n.pop();break}r=r.slice(1)}return{heartbeatsToSend:n,unsentEntries:r}}class Wt{constructor(e){this.app=e,this._canUseIndexedDBPromise=this.runIndexedDBEnvironmentCheck()}runIndexedDBEnvironmentCheck(){return h(this,null,function*(){return Re()?Me().then(()=>!0).catch(()=>!1):!1})}read(){return h(this,null,function*(){if(yield this._canUseIndexedDBPromise){const n=yield kt(this.app);return n!=null&&n.heartbeats?n:{heartbeats:[]}}else return{heartbeats:[]}})}overwrite(e){return h(this,null,function*(){var n;if(yield this._canUseIndexedDBPromise){const s=yield this.read();return q(this.app,{lastSentHeartbeatDate:(n=e.lastSentHeartbeatDate)!==null&&n!==void 0?n:s.lastSentHeartbeatDate,heartbeats:e.heartbeats})}else return})}add(e){return h(this,null,function*(){var n;if(yield this._canUseIndexedDBPromise){const s=yield this.read();return q(this.app,{lastSentHeartbeatDate:(n=e.lastSentHeartbeatDate)!==null&&n!==void 0?n:s.lastSentHeartbeatDate,heartbeats:[...s.heartbeats,...e.heartbeats]})}else return})}}function Q(t){return ne(JSON.stringify({version:2,heartbeats:t})).length}function Gt(t){if(t.length===0)return-1;let e=0,n=t[0].date;for(let r=1;r<t.length;r++)t[r].date<n&&(n=t[r].date,e=r);return e}/**
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
 */function Jt(t){H(new w("platform-logger",e=>new nt(e),"PRIVATE")),H(new w("heartbeat",e=>new Vt(e),"PRIVATE")),S(A,F,t),S(A,F,"esm2017"),S("fire-js","")}Jt("");export{w as C,B as D,ae as E,v as F,nn as S,Y as _,Zt as a,b,tn as c,y as d,Mt as e,$t as f,en as g,H as h,Qt as i,_ as j,Ht as k,sn as l,an as m,Ft as n,rn as o,on as p,Qe as q,S as r,cn as s,Xt as t,Re as u,Me as v,Yt as w,qt as x};
