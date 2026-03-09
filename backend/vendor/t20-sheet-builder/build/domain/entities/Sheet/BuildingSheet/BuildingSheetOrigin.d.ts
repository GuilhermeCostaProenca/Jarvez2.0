import { type OriginInterface } from '../../Origin/Origin';
import { type SheetOriginInterface } from '../SheetOriginInterface';
import { type TransactionInterface } from '../TransactionInterface';
export declare class BuildingSheetOrigin implements SheetOriginInterface {
    private origin;
    constructor(origin?: OriginInterface | undefined);
    chooseOrigin(origin: OriginInterface, transaction: TransactionInterface): void;
    getOrigin(): OriginInterface | undefined;
}
