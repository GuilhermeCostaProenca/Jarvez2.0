import { Handler } from '../../../../../../../../common/handler/Handler';
import { type SerializedArcanistLineage } from '../../../../SerializedArcanist';
import { type ArcanistLineage } from '../ArcanistLineage';
export declare abstract class ArcanistLineageSerializedHandler<T extends SerializedArcanistLineage> extends Handler<SerializedArcanistLineage, ArcanistLineage> {
    protected abstract handle(request: T): ArcanistLineage;
}
