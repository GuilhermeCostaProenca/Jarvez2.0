import { Handler } from '../../../../../../common/handler/Handler';
import { type SerializedArcanistPath } from '../../SerializedArcanist';
import { type ArcanistPath } from '../ArcanistPath';
export declare abstract class ArcanistPathSerializedHandler<T extends SerializedArcanistPath> extends Handler<SerializedArcanistPath, ArcanistPath> {
    protected abstract handle(request: T): ArcanistPath;
}
