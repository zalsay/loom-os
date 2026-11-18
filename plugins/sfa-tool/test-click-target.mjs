import test from 'node:test';
import assert from 'node:assert/strict';
import { argumentsFor } from './index.js';

const connection = 'D1BB8BA7-82DA-49D0-ABC4-BE546E6DD236';

test('JEV click uses the owned connection and forwards the target once without a frame', () => {
  const target = '打开「封面 01」';
  assert.deepEqual(argumentsFor({action:'click-target', target, frame:'', x:0, y:0}, connection),
    ['click-target', '--connection', connection, '--target', target]);
  assert.throws(() => argumentsFor({action:'click-target', target}, null), /connection/i);
  assert.throws(() => argumentsFor({action:'click-target', target, frame:connection}, connection), /frame/i);
});

test('JEV click requires target text and does not change coordinate click', () => {
  assert.throws(() => argumentsFor({action:'click-target'}, connection), /target/i);
  assert.throws(() => argumentsFor({action:'click-target', target:'  '}, connection), /target/i);
  assert.deepEqual(argumentsFor({action:'click', frame:connection, x:25, y:42, target:''}, connection),
    ['click', '--connection', connection, '--frame', connection, '--x','25','--y','42','--count','1']);
});
