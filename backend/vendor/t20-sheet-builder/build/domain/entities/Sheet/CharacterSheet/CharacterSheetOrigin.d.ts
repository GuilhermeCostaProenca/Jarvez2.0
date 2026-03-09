import { type OriginInterface } from '../../Origin/Origin';
import { type SheetOriginInterface } from '../SheetOriginInterface';
export declare class CharacterSheetOrigin implements SheetOriginInterface {
    private readonly origin;
    constructor(origin: OriginInterface);
    getOrigin(): OriginInterface;
}
