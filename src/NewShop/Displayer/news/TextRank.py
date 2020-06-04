#-*- coding:utf-8 -*-

from konlpy.tag import Komoran
import numpy as np
import pandas as pd


# TextRank is a graph-based model
class Graph(dict):
    def __init__(self):
        super(Graph, self).__init__()
        self.edge_weight = {}

    def add_vertex(self, v):
        if v in self.edge_weight.keys():
            pass
        else:
            self.edge_weight[v] = {}

    def add_edge(self, e, w):
        u, v = e
        if u in self.edge_weight[v].keys() and v in self.edge_weight[u].keys():
            pass
        else:
            self.edge_weight[u][v] = w
            self.edge_weight[v][u] = w

    def del_edge(self, e):
        u, v = e
        if not u in self.edge_weight[v].keys() and not v in self.edge_weight[u].keys():
            pass
        else:
            del self.edge_weight[v][u]
            del self.edge_weight[u][v]

    def del_vertex(self, v):
        if not v in self.edge_weight.keys():
            pass
        else:
            u = self.edge_weight[v].keys().copy()
            for _u in u:
                self.del_edge((v, _u))
            del self.edge_weight[v]

    def mod_edge_weight(self, e, w):
        u, v = e
        if not u in self.edge_weight.keys() and not v in self.edge_weight.keys():
            pass
        elif not v in self.edge_weight[u].keys() and not u in self.edge_weight[v].keys():
            pass
        else:
            self.edge_weight[u][v] = w
            self.edge_weight[v][u] = w


# Korean tokenizer
def komoran_tokenizer(sent):
    komoran = Komoran()
    # POS tagger
    tokens = komoran.pos(sent)
    # Interested only in Noun(NNP, NNG), Verb(VV, VX), Adjective(VA, VX)
    tokens = [token for token in tokens if 'NN' in token[1] or 'VV' in token[1] or 'VX' in token[1] or 'VA' in token[1]]
    return tokens


# TextRank uses co-occurence relation to make useful connection (edge)
def cooccurence_relation(tokens, window=2):
    # The window size is between 2 and 10.
    assert 2 <= window <= 10

    g = Graph()
    # Add all the token to the graph
    for token in tokens:
        g.add_vertex(token)
    # Connect edges to another tokens if the token co-occur with thems within a given window size
    for i, token in enumerate(tokens):
        start = max(0, i - window)
        end = min(len(tokens), i + window)
        for j in range(start, end):
            if token != tokens[j]:
                # Unweighted graph
                g.add_edge((token, tokens[j]), 1)

    # Maybe add min co-occurence
    return g


# TextRank uses similarity relation to make useful connection (edge)
# Here, uses TextRank similarity function as a similarity function. Cosine similarity function can be a similarity function as well.
def similarity_relation(sents):
    g = Graph()
    # Add all the sentences to the graph
    for sent in sents:
        g.add_vertex(sent)
    # Add tokens of all sentences to a list
    all_tokens = []
    for sent in sents:
        all_tokens += [komoran_tokenizer(sent)]
    # Connect edges to another sentence with weight (score)
    for i in range(len(all_tokens)):
        for j in range(len(all_tokens)):
            if i == j:
                pass
            else:
                rep_tokens = list(set([token for token in all_tokens[i] if token in all_tokens[j]]))
                score = len(rep_tokens) / (len(all_tokens[i]) + len(all_tokens[j]))
                g.add_edge((sents[i], sents[j]), score)

    return g


# Google's PageRank (Brin adn Page, 1998) algorithm
def pagerank(graph, d_f=0.85, epochs=30, threshold=0.001):
    assert 0 < d_f < 1
    assert 20 <= epochs <= 30

    # Set the initial value of score associated with each vertex to 1
    scores = dict.fromkeys(graph.edge_weight.keys(), 1.0)
    # Page ranking algorithm with iterations(epochs)
    for i in range(epochs):
        convergence = 0
        for j in graph.edge_weight.keys():
            score = 1 - d_f
            for k in graph.edge_weight[j].keys():
                # Weighted graph
                score += d_f * scores[k] * graph.edge_weight[j][k] / len(graph.edge_weight[k].keys())
            # Check with the threshold
            if abs(scores[j] - score) <= threshold:
                convergence += 1

            scores[j] = score

        # Early stopping
        if convergence == len(scores):
            break

    return scores


def keyword_extractor(sents, window=2, d_f=0.85, epochs=30, threshold=0.001, T=20):
    tokens = sum([komoran_tokenizer(sent) for sent in sents], [])
    graph = cooccurence_relation(tokens, window)
    scores = pagerank(graph, d_f, epochs, threshold)
    scores_list = list(scores.keys())
    score_order = np.argsort(list(scores.values()))[::-1]
    # The tokens that has high scores be the key words
    _key_words = np.asarray(scores_list)[score_order[:T]]
    return _key_words


def keysentence_summarizer(sents, d_f=0.85, epochs=30, threshold=0.001, T=3):
    graph = similarity_relation(sents)
    scores = pagerank(graph, d_f, epochs, threshold)
    scores_list = list(scores.keys())
    score_order = np.argsort(list(scores.values()))[::-1]
    # The tokens that has high scores be the key words
    _key_sentences = np.asarray(scores_list)[score_order[:T]]
    return _key_sentences


def test():
    # 기사출처: http://it.chosun.com/site/data/html_dir/2020/05/06/2020050601964.html
    sents = ['HTC 바이브(VIVE)가 업계 최초의 모듈형 가상현실(VR) 헤드셋 ‘바이브 코스모스 엘리트(VIVE Cosmos Elite)’를 정식으로 출시한다.', '바이브 코스모스 엘리트는 업계 최상급의 화질과 성능을 제공하는 바이브 코스모스 헤드셋(HMD)과 베이스 스테이션 1.0, 바이브 컨트롤러로 구성된 패키지 상품이다.', '외부 베이스 스테이션을 이용한 아웃사이드-인 트래킹을 지원하는 익스터널 트래킹 페이스 플레이트를 제공, 높은 정밀도와 위치 정확도를 요구하는 VR 마니아 및 전문가들을 위한 제품이다.', '베이스 스테이션 2.0 및 바이브 컨트롤러 2018과도 호환되어 더욱 확장된 규모의 VR 환경을 구현할 수 있다.', '국내 공식 공급원 제이씨현시스템을 통해 7일부터 VIVE 공식 몰 ‘바이브닷컴’과 바이브 액세서리 전문몰 ‘바이브스토어’에서 판매를 시작한다.', '기본 바이브 제품군 이용자가 업그레이드할 수 있도록 헤드셋만 별도로 선보일 예정이다.', '이와 더불어 HTC 바이브와 제이씨현은 6일 오후 3시부터 바이브 코스모스 엘리트의 ‘버추얼 런칭 간담회’를 진행한다.', '가상현실 공간에서 진행하는 신제품 출시 간담회로, HTC 바이브 코리아 공식 페이스북을 통해 생중계할 예정이다.', '바이브 코스모스 엘리트와 더불어 새로운 엔터프라이즈 VR 협업 애플리케이션 ‘바이브 싱크(VIVE Sync)’를 선보인다.']
    key_words = keyword_extractor(sents, window=2, d_f=0.85, epochs=30, threshold=0.001, T=20)
    print(key_words)
    # Output: [['바이브' 'NNP'] ['코스모스' 'NNP'] ['공식' 'NNG'] ['헤드셋' 'NNP'] ['엘리트' 'NNP'] ['베이스' 'NNP'] ['수' 'NNB'] ['제공' 'NNG'] ['스테이션' 'NNP'] ['킹' 'NNG'] ['트' 'VV'] ['일' 'NNB'] ['더불' 'VV'] ['간담회' 'NNG'] ['몰' 'VV'] ['통하' 'VV'] ['가상현실' 'NNP'] ['업계' 'NNG'] ['예정' 'NNG'] ['출시' 'NNG']]

    key_sentences = keysentence_summarizer(sents, d_f=0.85, epochs=30, threshold=0.001, T=3)
    print(key_sentences)
    # Output: ['HTC 바이브(VIVE)가 업계 최초의 모듈형 가상현실(VR) 헤드셋 ‘바이브 코스모스 엘리트(VIVE Cosmos Elite)’를 정식으로 출시한다.' '바이브 코스모스 엘리트는 업계 최상급의 화질과 성능을 제공하는 바이브 코스모스 헤드셋(HMD)과 베이스 스테이션 1.0, 바이브 컨트롤러로 구성된 패키지 상품이다.' '이와 더불어 HTC 바이브와 제이씨현은 6일 오후 3시부터 바이브 코스모스 엘리트의 ‘버추얼 런칭 간담회’를 진행한다.']


def make_dataset():
    sents_ = [['서버용 D램 가격이 각 국의 ‘언택트’ 수요에도 불구하고 제자리걸음을 하며 업계의 불안이 커지고 있다.', '신종코로나바이러스감염증(코로나19) 확산에 따른 반도체 특수가 각 국의 인력이동 제한 조치 및 공장 가동 어려움으로 사실상 끝난것이 아니냐는 분석까지 나온다.', '30일 시장조사기관인 D램 익스체인지에 따르면 이달 서버용 D램 DDR4 32GB 고정거래 가격은 143.1달러로 지난달과 같았다.', '지난 4월 서버용 D램 가격 상승률이 18%에 달했다는 점에서 연초부터 이어져 오던 상승세가 멈춘 셈이다. 서버용 D램은 지난해 말 1개당 106.0달러를 기록한 후 올 1월(109.0달러), 2월(115.5달러), 3월(121.3달러), 4월(143.1달러) 등 매월 꾸준히 상승한 바 있다.', '이달 PC용 D램 고정거래 가격은 1개당 3.31달러를 기록했다. 전월(3.29달러) 대비 0.6% 오르는데 그쳤으며 지난해 6월과 가격이 같다. 지난 2018년 9월 가격(8.19달러)의 절반에도 못 미친다.', '김선우 메리츠증권 연구원은 “재택근무 활성화로 비디오스트리밍 수요 등이 증가하면서 클라우드 업체들의 수요 강세가 관찰됐으나 동남아에 자리한 각 업체들의 공장(서플라이 체인)이 완전히 회복되지 않아 D램 출하 속도가 둔화돼 가격 상승이 제한됐다”고 밝혔다.'],
    ['서버용 D램 가격이 각 국의 ‘언택트’ 수요에도 불구하고 제자리걸음을 했다.', '신종코로나바이러스감염증(코로나19) 확산에 따른 반도체 특수가 각 국의 인력이동 제한 조치 및 공장 가동 어려움으로 사실상 끝난것이 아니냐는 우려가 나온다.', '29일 시장조사기관인 D램 익스체인지에 따르면 이달 서버용 D램 DDR4 32GB 고정거래 가격은 143.1달러로 지난달과 같았다.', '지난 4월 서버용 D램 가격 상승률이 18%에 달했다는 점에서 연초부터 이어져 오던 상승세가 멈춘 셈이다.', '서버용 D램은 지난해 말 1개당 106.0달러를 기록한 후 올 1월(109.0달러), 2월(115.5달러) 등 매월 꾸준히 상승한 바 있다.', '김선우 메리츠증권 연구원은 “재택근무 활성화로 비디오스트리밍 수요 등이 증가하면서 클라우드 업체들의 수요 강세가 관찰됐으나 동남아에 자리한 각 업체들의 공장(서플라이 체인)이 완전히 회복되지 않아 D램 출하 속도가 둔화돼 가격 상승이 제한됐다”며 “공급사들은 하반기에 고용량 모듈(64GB) 생산 비율을 높이리라 예상하며 최근 한국 D램업체들이 비용 최적화를 달성하기 위해 공정 전환에 속도를 내는 모습”이라고 밝혔다.', '삼성전자(005930)와 SK하이닉스(000660) 등의 D램 공급사들은 제품 생산 수율 향상으로 올 하반기에는 D램 공급량을 추가로 늘릴 것으로 전망된다.', '다만 D램익스체인지는 올 3분기 서버용 D램 판매가격이 제자리 걸음을 할 것이라 예상하는 등 시장 상황이 좋지 않다.', '올 4분기 서버용 D램 가격은 공급량 증가에 따라 10% 가량 하락할 것이란 전망도 나온다.', 'PC용 D램 현물가격의 추이도 좋지않다.', 'D램익스체인지에 따르면 PC용 D램(DDR4 8Gb 기준) 1개당 가격은 이날 3.06달러를 기록했다.', "‘언택트’ 경제 활성화로 PC용 D램 수요가 급증했던 지난달 초 가격인 3.63달러와 비교해 20% 가량 떨어졌다.", '특히 지난달 8일부터 가격 하락 추이가 계속돼 올 1월 3일 기록했던 가격(3.05달러) 수준까지 내려왔다.', 'PC용 D램은 서버와 모바일에 이어 D램 시장의 약 18% 가량을 차지하는 중요 시장이다.', '업계에서는 현물가격 추이가 고정거래가격의 선행지표 역할을 한다는 점에서 반도체 가격이 전반적으로 하락할 수 있다는 분석도 내놓는다.', '낸드플래시 고정거래가격(128Gb MLC 기준) 또한 두달째 제자리 걸음을 해 이달 4.68달러를 기록했다.', '업계에서는 서버용 SSD에 강점이 있는 삼성전자를 제외하고는 여타 낸드플래시 업체들이 수익을 내지 못하는 것으로 보고있다.', '반도체 업계 관계자는 “코로나19에 따른 파장에 미중 무역분쟁 관련 불확실성 등 반도체 업황에 부정적 환경이 조성되고 있다”며 “자동차, 정유, 화학 등 주요 산업이 모두 흔들리는 가운데 반도체 경기마저 흔들릴 경우 국내 경기성장률 예상치 추가 인하가 불가피해 보인다”고 밝혔다.'],
    ['코로나19 확산에도 언택트(비대면) 활동이 늘어나면서 D램 가격이 급등했다.', '재택근무와 온라인 수업 실시로 데이터센터 서버 수요가 증가하면서 D램 가격이 지난달 크게 상승한 것으로 나타났다.', '4일 업계와 시장조사업체인 디램익스체인지에 따르면 개인용 컴퓨터(PC)에 주로 사용되는 DDR4 8기가비트(Gb) D램 제품의 고정거래 계약 평균 가격은 지난달 말 기준 3.29달러로 전월(2.94달러)에 비해 11.9% 상승했다.', 'D램 가격의 월별 상승률이 두 자릿수를 나타낸 것은 지난 2017년 4월 이후 약 3년만이다.', '또 D램 가격이 3달러선에 올라선 것도 지난 2019년 6월 이후 10개월만이다.', '올해 D램 가격은 지난 1월 전월보다 1.07% 상승한 2.84달러를 기록한 이후 줄곧 상승세를 보이고 있다.', '지난해 말까지 이어진 글로벌 반도체 시황 둔화를 지나 올해부터 가격 상승을 시작했고, 최근엔 코로나19 여파로 상승폭이 확대된 것으로 해석된다.', '데이터센터 업체들이 재택근무와 온라인 수업 등으로 인해 늘어난 수요에 맞춰 서버를 증설하면서 메모리 반도체 판매가 늘어났다는 설명이다.', '아울러 업계에선 코로나19로 가동이 중단됐던 중국 PC제조사들이 본격 생산라인을 움직이면서 메모리 반도체 주문량이 급격히 늘어난 것으로 보고 있다.', '삼성전자 등 메모리 반도체 업체들은 클라우드 등 데이터센터 서버를 활용한 서비스가 다양해지고 활발해짐에 따라 D램 등 메모리 반도체 수요도 지속될 것으로 전망하고 있다.', '다만 솔리드스테이트드라이브(SSD)에 쓰이는 낸드플래시 가격은 변동이 없었다.', '128기가비트(Gb) 멀티 레벨 셀(MLC) 제품 가격이 지난달 기준으로 4.68달러를 기록하며 전월과 동일했다.', '스마트폰 등 모바일용 수요가 줄었지만 전체 시장의 수요와 공급이 균형을 이루면서 변동이 없었던 것으로 분석된다.'],
    ['해 반도체 불황이 덮치며 차세대 저장 장치로 불리는 솔리드 스테이트 드라이브(SSD) 수출도 1년 새 "반 토막" 난 것으로 나타났다.', '22일 한국전자정보통신산업진흥회(KEA)에 따르면 국내 SSD의 올해 1∼3분기 누적 수출액은 31억3천700만달러(약 3조7천억원)로 작년 같은 기간보다 46.9% 줄어들었다.', '메모리 반도체(품목번호 HSK854232) 수출이 같은 기간 35.9% 줄어든 것과 비교해도 가파른 감소세다.', 'SSD는 메모리 반도체를 사용하는 대용량 저장 장치로 기존 하드 디스크 드라이브(HDD)를 대체할 차세대 제품으로 꼽힌다.', '올해 데이터센터를 중심으로 서버용 SSD 수요가 크게 줄어들면서 수출에 부정적 영향을 미쳤을 것이란 게 업계 분석이다.', '글로벌 시장조사업체 IHS마킷에 따르면 올해 3분기 글로벌 SSD 시장 규모는 작년 동기 대비 27.9% 감소했고, SSD 평균 가격도 38.4% 하락했다.', '업계 관계자는 "서버용 SSD는 모바일용보다 용량이 크다 보니 수익성이 높은 편"이라며 "서버용이 비중이 줄고 모바일용이 늘어나면서 수출액도 줄어들었을 것"이라고 설명했다.', '다만 수출액 감소 폭은 1분기 55.6%, 2분기 53.1%에서 3분기 30.0%로 줄어드는 추세다.','단가 하락에 따라 수요가 늘어나면서 데이터센터 업체 등 수요 기업들의 재고도 줄어들기 시작한 것으로 분석된다.', '이에 따라 SSD 시장 1위를 지키고 있는 삼성전자[005930] 또한 내년께 관련 실적 회복을 기대할 수 있게 됐다.', '앞서 삼성전자는 지난 9월 소프트웨어 혁신기술 3개를 적용한 초고용량 4세대 SSD 신제품 19종을 출시하며 글로벌 시장 위축에도 적극적인 모습을 보였다.', 'SK하이닉스[000660]는 10월 일반 소비자용 SSD 시장에도 뛰어들면서 선발주자를 추격하고 있다. 올해 2분기 점유율은 4.0%로 업계 6위 수준이다.', '한편 IHS마킷에 따르면 올해 2분기 기준 SSD 시장 점유율 1위는 삼성전자(30.6%), 2위는 인텔(17.4%), 3위는 웨스턴디지털(11.2%)이다.'],
    ['ASUS 메인보드 공식유통사인 에스티컴퓨터(대표 : 서희문, 이하 STCOM)는 화이트 컬러 컨셉을 최초로 도입한 ROG STRIX 신 라인업 제품인 ASUS ROG STRIX Z490-A GAMING 신제품을 출시했다고 밝혔다.', '이러한 새로운 컬러 도입에 맞춰 ROG STRIX 시리즈의 라인업 등급도 기존 -E, -F, -H 등급에 더해 -A 등급이 새롭게 추가되었다.', '프리마운트 IO 쉴드에는 강력한 성능과 OC 지원능력을 상징하는 ROG 로고와 AURA SYNC 효과를 지원하는 LED가 적용되어 강인함과 세련된 화이트 컬러와의 디자인 감각을 보여준다.', '오버클러킹 등을 하다가 문제가 생기거나 기타 설정에 문제가 있는 경우 바이오스를 초기화해야 하는 경우가 발생한다.', '이러한 상황 발생시 ASUS ROG STRIX Z490-A GAMING에는 후면 IO포트에 바이오스 플래시백 버튼을 통해서 손쉽게 바이오스를 복구할 수 있도록 지원한다.', '사용자층이 점점 넓어지고 있는 USB 타입 C 포트는 물론 동작속도 별로 쉽게 구분하여 사용할 수 있도록 컬러로 구분된 USB 포트가 제공된다.', '사운드 출력 부분에서는 디지털 사운드 규격인 SPDIF 대응이 가능하며 각각의 출력포트에도 금도금 처리를 하여 최상의 사운드 품질을 들을 수 있도록 지원한다.', '고급형 메인보드에서 보편화되고 있는 RGB 주변기기 연결을 위한 RGB 포트 설계에서도 세심한 설계가 돋보이는데 PCB 기판의 가장 상단과 가장 하단위치 2곳에 각각 RGB 헤더를 나눠서 위치하도록 하여 보다 손쉽게 RGB 튜닝이 가능하도록 한다.', '3개의 PCI express 그래픽카드 지원 슬롯 중 가장 상단에 위치한 슬롯은 두께가 두꺼운 대형 그래픽카드 장착을 고려하여 다음 슬롯과의 간격을 기존 보다 2배 더 넓게 잡아 고성능 그래픽카드의 장착에 최적화하도록 설계되었다.', '또한 각각의 PCI-Express 슬롯에는 무게가 무거운 그래픽카드를 장착하여 장시간 사용하더라도 강인한 내구성을 가지도록 한 그래픽카드 보강기술인 ASUS Safe Slot 기술이 적용되었다.', '스토리지 지원부분에서도 ASUS ROG STRIX Z490-A GAMING가 매우 세심하게 설계된 제품이라는 부분을 알 수가 있다.', 'M.2 SSD는 방열판이 기본 장착된 경우와 그렇지 않은 경우로 나눠지는데 2가지 타입의 M.2 SSD에 모두 대응되도록 방열판이 지원되는 M.2 슬롯과 그렇지 않은 M.2 슬롯의 구성을 적용하고 있다.', '또 M.2 방식을 사용하는 Wi-Fi 주변기기를 위한 전용 M.2 슬롯도 함께 제공하여 사용자가 보다 다양한 장치를 사용할 수 있도록 해준다.', 'SATA 포트의 경우는 2층으로 적층하지 않고 6개의 포트를 1열로 배치하여 케이블의 연결편의성은 물론 SATA 장치와 연결된 기기를 보다 쉽게 구분할 수 있도록 설계되었다.', '사용자가 실제로 사용하는 상황을 매우 세심하게 고려하여 최적의 편의성을 제공하는 설계가 적용된 것이다.', '메인 전원 포트에는 4개의 모니터링 LED가 장착되어 각각 BOOT, VGA, DRAM, CPU 등의 핵심 부품의 상태 모니터링을 사용자가 시각적으로 쉽게 파악할 수 있도록 해준다.', '기타 보다 자세한 제품 정보는 STCOM 홈페이지 등을 참조하면 된다.'],
    ['인텔이 자사의 옵테인 기술을 활용해, 메모리와 스토리지 기술을 결합한 M.2 커넥터용 제품을 개발했다.', '제품은 최대 32GB 캐시의 옵테인 메모리와 1TB급 SSD 성능의 QLC 스토리지를 포함한다.', '인텔은 새로운 제품을 노트북 OME에 먼저 공급할 계획이다.', '하나의 M.2 슬롯에 메모리와 스토리지를 포함한 제품을 통해, 고성능의 경량화 노트북 개발이 가능하기 때문이다.', '인텔은 델(Dell), HP, 에이수스(ASUS), 에이서(Acer) 등이 해당 제품을 채용한 노트북을 준비하고 있다고 밝혔다.', '11일 인텔은 자사의 옵테인 기술과 쿼드레벨셀(QLC) 3D 낸드 기술을 단일 M.2 커넥터용으로 결합시킨 혁신적인 ‘인텔 옵테인 메모리 H10 솔리드 스테이트 스토리지(Solid State Storage)’를 발표했다.', '롭 크룩(Rob Crooke) 인텔 수석 부사장 겸 비휘발성 메모리 솔루션 그룹 총괄은 “인텔 옵테인 메모리 H10 솔리드 스테이트 스토리지는 인텔 옵테인 기술과 인텔 QLC 3D 낸드의 특별한 조합으로 구성됐으며, 다른 누구도 제공할 수 없는 인텔 커넥티드 플랫폼의 강점을 기반으로하는 메모리와 스토리지에 대한 인텔만의 혁신적인 접근 방식을 보여준다”라고 말했다.', '제품은 하나의 M.2 모듈로 결합해, 가볍고 얇은 노트북과 올인원 PC 및 미니PC와 같이 공간 제약이 있는 데스크톱에 인텔 옵테인 메모리 확장을 가능하게 한다.', '또한, QLC 3D 낸드 기술을 제공하기 때문에 보조 스토리지가 필요 없다.', '인텔은 새로운 제품이 독립형 TLC 3D 낸드 SSD 시스템과 비교해, 자주 이용하는 애플리케이션과 파일에 더욱 빠른 액세스와 백그라운드 활동에 더욱 뛰어난 응답성을 제공한다고 설명한다.', '옵테인 메모리가 탑재된 인텔 기반 플랫폼은 이용자의 가장 보편적인 컴퓨팅 작업과 자주 사용되는 애플리케이션에 대한 성능을 최적화하는 일반적인 컴퓨팅 활동에 적합하다는 것이다.', '또한, 최대 총 1TB까지 제공되는 SSD 급의 스토리지로 사용자들에게 충분한 용량을 제공한다.', '제품은 ▲16GB(인텔 옵테인 메모리) + 256GB(스토리지) ▲32GB(인텔 옵테인 메모리) + 512GB(스토리지) ▲32GB(인텔 옵테인 메모리) + 1TB(스토리지) 등 세가지 옵션으로 구성된다.', '신 제품이 탑재된 8세대 인텔 코어 U시리즈 모바일 플랫폼은 2분기 말부터 주요 노트북 OEM을 통해 제공될 예정이다.', '델, HP, 에이수스, 에이서를 포함한 다양한 노트북 OEM을 통해 초기 시스템 구매를 할 수 있다. 또한, 베스트 바이(Best Buy), 코스트코(Costco)에서도 구매할 수 있다.'],
    ['낸드 플래시 제조사로 유명한 마이크론에서 3D 낸드를 적용한 최신 SSD를 출시했다.', '이번에 마이크론에서 새롭게 선보이는 크루셜 MX500 시리즈 SSD는 지난해 많은 사용자에게 뛰어난 성능과 안정성으로 인기를 얻었던 "MX 300" 시리즈의 후속작으로 나온 제품이며, 더욱 발전된 TLC 64단 3D 낸드와 컨트롤러를 탑재해 성능을 높이고 가격을 유지한 제품이다.', '케이벤치에서는 마이크론 크루셜 MX500 SSD에 대한 자세한 성능을 알아보는 시간을 가져볼까 한다.', '현재, SSD의 트렌드는 바로 TLC구조의 64단 3D 낸드가 대세다. 최근 삼성전자, 샌디스크 등 SSD 등 다양한 제조사에서 나오는 SSD 제품을 살펴보면 알 수 있다.', '마이크론사에서도 이에 맞춰 TLC 64단 3D 낸드를 적용한 크루셜 MX500 시리즈를 출시하였으며, 이전 MX300 시리즈에 비해서 개선된 공정으로 전반적인 성능과 안정성이 개선된 제품이다.', '마이크론 크루셜 MX500 시리즈는 기존 MX300 시리즈 SSD 제품의 읽기 성능이 530MB/s, 쓰기 성능이 510MB/s이었던 것에 비해 MX500 SSD 제품은 읽기 성능 560MB/s, 쓰기 성능 510MB/s로 성능이 향상되었다.', '일반적인 PC 환경에서 성능의 차이를 느낄 수 있는 4K 랜덤 읽기, 4K 랜덤 쓰기 IOPS의 성능도 랜덤 읽기 95K, 랜덤 쓰기 90K로 향상됐다.', '그리고 마이크론 크루셜 MX500 시리즈는 성능뿐만 아니라 안정성 측면에서도 더욱 발전된 모습을 보여준다.', '제조사에서 보장하는 사용보증 시간은 1,500,000 시간에서 1,800,000 시간으로 늘어났으며, SSD 수명 척도로 자주 쓰이는 총 데이터 쓰기량은 160TB에서 180TB로 향상된 수명을 지녔다.', '워런티 기간도 기존 3년에서 5년으로 늘어났다. 이에 제품 내구성 및 수명뿐만 아니라 안정적인 A/S도 보증하고 있다.', '마이크론 MX300은 마벨 88SS1074 컨트롤러를 사용했지만 이번에 출시된 마이크론 MX500 시리즈 SSD는 실리콘모션 SM2285 컨트롤러를 채택했다.', '실리콘모션 SM2258의 특징은 낸드익스텐드(NANDXtend) 기술과 데이터 무결성을 보장하는 레이드(RAID) 보호 기술, LDPC 디코딩 기술을 바탕으로 3D TLC 낸드(NAND)의 쓰기/지우기 주기를 향상시켜 SSD 수명을 연장시켜준다.', '또한, AES 256, TCG 및 Opal 2.0 드라이브 암호화 기준 등 다양한 보안 프로토콜을 지원해 보안성이 향상됐다.', '이번에 적용된 칩셋은 자체적인 커스텀 펌웨어를 통해 100mW의 저전력으로 구동되어 발열을 줄여서 전력 소모에 민감한 넷북 등에서 보다 오랜 시간 구동이 가능하다.', '대기 전력을 최대한 줄일 수 있는 "DevSleep" 기술을 적용해 4mW로 대기 전력 소모도 개선되어 저전력을 구현한 제품이다.'],
    ['홍콩 소재 컴퓨터 메모리 제조•판매업체 에센코어(ESSENCORE)의 글로벌 하우스 브랜드 클레브(KLEVV)가 NEO N610 2.5” SATA SSD 출시를 앞두고 있다.', '에센코어는 최근 “성능과 신뢰성, 보안을 모두 강화한 NEO N610 2.5” SATA SSD를 출시했다”며 “사무 업무 뿐 아니라 크리에이션, 게이밍 등 다양한 상황에서 최적의 작업 환경을 제공하는 기술 선도적 품질의 저장장치로 사용자들이 만족하는 제품이 될 것”이라고 말했다.', 'KLEVV NEO N610은 SATA Revision 3.1 인터페이스 및 2.5인치 7㎜ 규격 폼팩터가 적용 되었다. 256GB, 512GB, 1TB 총 3가지 대용량으로 출시되어 사용자의 편의성을 높였으며, 엄격히 선별된 3D 낸드 플래시를 사용한다.', '전용량 최대 읽기 속도 560MB/s, 최대 쓰기 속도 520MB/s으로 빠른 시스템 속도를 제공하며, 4채널 컨트롤러 IC 기반으로 데이터 효율을 개선해 대역폭을 확대함과 동시에 대용량 데이터 전송이 가능하다.', '특히 NEO N610은 DRAM 내장형 SSD로, 제품의 수명을 연장하고, 실행 속도를 향상시키는 동시에 내구성을 강화한 가성비 최고의 저장장치라고 할 수 있다.', '한 단계 더 엄격해진 검사 과정을 통해 KLEVV NEO N610 SSD는 완벽한 충격 및 떨림방지 기능을 확보, 견고함을 자신한다.', '이 외에도 기존의 문제점을 개선한, 향상된 통합 플래시 매니지먼트를 지원받을 수 있다.', '특히 오버-프로비젼과 배드블록 관리 기능으로 제품 수명 연장과 함께 장시간 사용이 가능하다.', '안정성을 높이기 위한 S.M.A.R.T(자체모니터링, 분석 및 보고), TRIM 기술이 각각 적용되어 최상의 제품 성능이 유지된다.', '해당 제품 구매자들은 에센코어 공식 홈페이지 내 KLEVV 데이터 마이그레이션 소프트웨어 센터를 통해 Acronis True Image HD 2018 활성화 키를 다운받을 수 있다.', '디스크 이미지 백업 및 복원 기능과 데이터의 매끄러운 전송을 지원하는 소프트웨어로, 사용자는 기존 하드 디스크 내용을 새 SSD 드라이브에 쉽고 빠르게 복사할 수 있다.', 'KLEVV의 SSD는 세계 각국의 국가인증을 받아 언제 어디서든 믿고 사용할 수 있다.', 'SK그룹 자회사인 에센코어는 메모리 모듈이나 플래시 메모리, SSD의 제조 판매하고 있다.', '에센코어는 글로벌 하우스 브랜드 ‘클레브(KLEVV)’를 통해 소비자들에게 게이밍 OC 메모리, 스탠다드 DRAM 메모리, SSD와 SD카드, USB 등 메모리 제품을 선보이고 있다.'],
    ['홍콩 소재 컴퓨터 메모리 제조·판매업체 에센코어(ESSENCORE)의 글로벌 하우스 브랜드 클레브(KLEVV)에서 5월 18일(월) 단 하루 동안 11번가 ‘긴급공수’ 특가 프로모션을 실시한다고 전했다.', '행사 당일, 11번가에서 KLEVV NEO N400 SSD를 구매하는 전 고객들은 14% 특가 혜택을 받을 수 있으며, 현대카드 고객들은 쿠폰 적용을 통해 더욱 더 저렴하게 제품 구매가 가능하다.', '에센코어의 KLEVV NEO N400 SSD는 가성비가 훌륭한 SSD 저장장치로 인기를 끌고 있다. 여러 차례 퀘이사존 채널 벤치마크 테스트를 통해 보급형 SSD의 대표 제품으로 증명된 바 있다.', 'NEO N400 SSD는 SATA Revision 3.2 (SATA 6Gb/s) 인터페이스와 2.5인치 규격의 제품으로 데스크톱 구성에 알맞은 제품이다.', '또한 보급형120GB부터 부담 없이 사용 가능한 240GB, 그리고 필요한 모든 작업이 가능한 480GB까지 다양한 용량 라인업으로 사용자의 편의성을 높였다.', '전용량 최대 읽기 속도 500MB/s로 시스템 활용에 최적화되어 있으며, 한 단계 더 엄격해진 검사과정을 통해 완벽한 충격 및 떨림 방지 기능을 확보, 누구나 안심하고 사용할 수 있다.', '11번가 긴급공수 당일 해당 제품 구매자들은 모두 에센코어 공식 홈페이지 내 KLEVV 데이터 마이그레이션 소프트웨어 센터를 통해 Acronis True Image HD 2018 활성화 키를 다운받을 수 있다.', '디스크 이미지 백업 및 복원 기능과 데이터의 매끄러운 전송을 지원하는 소프트웨어로, 사용자는 기존 하드 디스크 내용을 새 SSD 드라이브에 쉽고 빠르게 복사할 수 있다.', 'SK그룹 자회사인 에센코어는 메모리 모듈이나 플래시 메모리, SSD의 제조 판매하고 있다.', '에센코어는 글로벌 하우스 브랜드 ‘클레브(KLEVV)’를 통해 소비자들에게 게이밍 OC 메모리, 스탠다드 DRAM 메모리, SSD와 SD카드, USB 등 메모리 제품을 선보이고 있다.', '오는 18일 단 하루 동안 진행되는 이번 KLEVV의 ‘긴급공수’ 관련 자세한 정보는 11번가 쇼킹딜 페이지 및 KLEVV SNS 채널을 통해 확인이 가능하다.'],
    ['삼성전자 공식 파트너사 유니씨앤씨는 대화면 QLED 디스플레이와 터치패드를 통한 무선 배터리 공유, 뛰어난 확장성 등 다양한 신기술이 적용된 초경량 초슬림 삼성전자 갤럭시북 이온 NT950XCR-A58A 모델을 대상으로 최대 24만원 추가 할인 및 푸짐한 사은품이 증정되는 긴급공수 프로모션을 5월 21일 단 하루 11번가를 통하여 단독 진행한다.', '이번 행사는 9% 선택할인 쿠폰과 5% 중복할인 쿠폰, 3% 카드할인, 2만원 장바구니 할인을 통하여 최대 24만원 할인 혜택을 받을 수 있으며, 최대 22개월 무이자 할부가 진행되어 삼성전자 갤럭시북 인기모델을 부담 없는 가격에 구입이 가능하다.', '또한, 제품 구매 시 삼성 혜택APP을 통하여 대성마이맥의 고3·N수 수능패키지, 시원스쿨의 기초 영어회화 / 어린이 영어, 다락원의 TOEIC / OIPc / 중국어 / 일본어 어학과정, IT/자격증 강의 등 310여개의 다양한 온라인 강의 콘텐츠를 1년 동안 무료 수강이 가능하다. 그리고 포토리뷰 작성 시 한컴오피스, 블루투스 이어폰, 노트북 백팩 등 다양한 사은품을 택일하여 받을 수 있으며 고객만족 서비스로 서울 전 지역에 한해 무료 퀵배송을 실시한다.'],
    ['롯데렌탈의 라이프스타일 렌탈 플랫폼 "묘미(MYOMEE)"는 최근 코로나19 사태 장기화로 대학의 비대면 온라인 강의가 연장됨에 따라 "노트북 장기렌탈 프로모션"을 진행한다고 12일 밝혔다.', '묘미의 노트북 장기렌탈은 초기 비용에 대한 부담이 적고, 구매 대비 최대 30% 저렴해 목돈 마련에 상대적으로 어려움을 느끼는 대학생들에게 특히 유용하다.', '제조사에서 제공하는 1년 무상 A/S 외에도 계약기간 동안 출장 및 원격 관리를 2회 무상 지원한다. 렌탈 계약이 종료된 후에는 개인정보 데이터 포맷 등 안심 서비스로 개인정보 유출에 대한 우려 없이 반납 가능해 안전하고 편리한 관리 서비스가 특징이다.', "오는 28일부터 대학생 선착순 100명 한정으로 진행되는 이번 노트북 장기렌탈 프로모션은 삼성전자의 최신 노트북 2종인 '갤럭시북 플렉스', '갤럭시북 이온'을 대상으로 한다.", "갤럭시북 플렉스와 갤럭시북 이온은 세계 최초로 노트북에 QLED 디스플레이를 탑재한 제품이다. 갤럭시북 플렉스는 가속도, 자이로 센서가 탑재된 'S펜'을 내장해 제스처 인식 기능을 지원하며, 360도 회전되는 터치스크린 디스플레이 탑재로 태블릿의 사용 경험까지 제공한다.", '갤럭시북 이온은 휴대성에 최적화된 제품이며, 39.6cm 모델은 확장가능한 메모리, 저장장치 슬롯을 제공해 사용자 필요에 따라 추가 장착이 가능한 확장성을 제공한다.', '이번 프로모션은 첫달 렌탈료 전액을 엘포인트(L.Point) 페이백으로 지급, 사실상 한달 간 무상으로 노트북 렌탈 서비스를 이용할 수 있다.', '더불어 삼성 무선 마우스, 노트북 전용 파우치와 같은 액세서리와 함께 스타벅스 모바일 쿠폰 등의 사은품이 지급된다.', '36개월 장기렌탈 월 렌탈료는 각각 갤럭시북 이온(i5 CPU, 8GB 메모리, 256GB SSD, 39.6cm 디스플레이) 4만9900원, 갤럭시북 플렉스(i7 CPU, 16GB 메모리, 512GB SSD, 39.6cm 디스플레이) 6만4700원이다.', '이번 노트북 장기렌탈 프로모션에서는 본인의 재학증명서 또는 학생증 증명을 통해 체크카드, 계좌이체 등 다양한 결제 수단을 선택할 수 있도록 했다.', '최근영 롯데렌탈 소비재렌탈부문장 상무는 "최근 대부분의 대학에 비대면 온라인 강의가 진행되며 노트북 구매를 고려하는 대학생이 늘고 있지만, 최신 성능의 제품을 선뜻 구매하긴 비용 부담이 만만치 않을 것이 사실"이라며 "이번 프로모션으로 대학생 한정의 다양한 혜택을 준비한 만큼, 노트북 장만의 좋은 기회가 되길 바란다"고 말했다.'],
    ['마이크론 크루셜(Micron Crucial) SSD의 공식 수입사 아스크텍이 2019년 황금돼지해를 맞아 자사가 유통하는 마이크론 크루셜 SSD의 특별 할인 프로모션을 진행한다고 16일 밝혔다.', '이번 행사 모델은 PCI 익스프레스 기반 고성능 NVMe SSD인 ‘크루셜 P1’ 시리즈를 대상으로 진행하는 것으로 행사 기간 500기가바이트(GB) 모델은 9만9000원에, 1테라바이트(TB) 모델은 19만9000원에 구매할 수 있다.', '마이크론 크루셜 P1 시리즈는 3차원 수직 구조를 적용한 차세대 3D QLC 낸드 플래시를 채택, 초소형 M.2 폼팩터에서 최대 2TB의 고용량을 구현한 것이 특징이다.', '성능도 2TB 모델 기준으로 최대 연속 읽기 2000MB/s, 연속 쓰기 1750MB/s로 기존 SATA 방식 SSD와 비교해 약 4배 빠른 읽기 속도와 3.5배 빠른 쓰기 성능을 제공한다.', '최대 25만 IOPS(초당입출력속도)의 랜덤 읽기 속도로 운영체제(OS)와 게임 등 각종 애플리케이션을 설치하고 빠르게 실행 및 다중 작업을 처리하기에 적합하다.', '이번 프로모션은 16일부터 온라인 쇼핑몰 11번가에서 단독으로 진행하며, 쇼핑몰의 아카데미 프로모션을 통해 추가 할인 혜택을 받을 수 있다.'],
    ['5월 PC용 D램(DDR4 8Gb 기준) 고정거래가격이 0.6% 오르는 데 그친데다 서버용 D램 가격은 제자리걸음이다.', '반도체 시장 회복 기대가 불안으로 다시 바뀌고 있다.', '일각에서는 신종코로나바이러스 감염증(코로나 19) 확산에 따른 ‘언택트’ 수요가 사실상 끝난 것이 아니냐는 분석도 제기된다.', '29일 시장조사기관인 D램익스체인지에 따르면 이달 PC용 D램 고정거래 가격은 1개당 3.31달러를 기록했다.', '전월(3.29달러) 대비 0.6% 올랐으며 지난해 6월과 가격이 같다. 지난 2018년 9월 가격(8.19달러)의 절반에도 못 미친다.', '반면 이달 서버용 D램 DDR4 32GB 고정거래 가격은 143.1달러로 지난달과 같았다.', '4월 서버용 D램 가격 상승률이 18%에 달했다는 점에서 연초부터 이어져 오던 상승세가 멈춘 셈이다.', '서버용 D램은 지난해 말 1개당 106.0달러를 기록한 후 올 1월(109.0달러), 2월(115.5달러), 3월(121.3달러), 4월(143.1달러)까지 매월 꾸준히 상승한 바 있다.', '일각에서는 이 같은 가격 상승세가 점차 둔화되고 하락세로 접어들 수 있다는 우려를 내놓는다.', 'PC용 D램(DDR4 8Gb 기준) 1개당 현물가격이 이날 3.06달러를 기록하며 업계 불안을 부추긴 탓이다.', '언택트 경제 활성화로 PC용 D램 수요가 급증했던 지난달 초 가격인 3.63달러와 비교해 20%가량 떨어졌다.', '특히 지난달 8일부터 가격 하락 추이가 계속돼 올 1월3일 기록했던 가격(3.05달러) 수준까지 내려왔다.', '업계에서는 현물가격 추이가 고정거래가격의 선행지표 역할을 한다는 점에서 반도체 가격이 전반적으로 하락할 수 있다는 분석도 내놓는다.', 'D램익스체인지 측은 “D램 공급사의 재고소진 노력에도 불구하고 D램 현물가는 하락세에서 당분간 반등하기 어려울 것”이라며 “이 같은 D램 현물가와 고정가 간의 가격차이 확대는 올 3·4분기 가격 협상시 판매가격 상승을 제한할 수 있는 요인”이라고 밝혔다.', '낸드플래시 고정거래 가격(128Gb MLC 기준) 또한 두 달째 제자리걸음을 해 이달 4.68달러를 기록했다.', '업계에서는 서버용 솔리드스테이트드라이브(SSD)에 강점이 있는 삼성전자(005930)를 제외하고는 여타 낸드플래시 업체들이 수익을 내지 못하는 상황에서 이 같은 낸드플래시 가격이 업황 개선의 발목을 잡을 것이라 보고 있다.', '최근에는 미중 무역분쟁으로 국내 반도체 업계의 최대 고객사 중 하나인 화웨이에 D램 등 메모리 반도체 공급을 못 할 수 있다는 분석이 제기돼 올 하반기 매출이 크게 꺾일 수 있다는 우려도 나온다.', '반도체 업계의 한 관계자는 “코로나19에 따른 파장에 미중 무역분쟁 관련 불확실성 등 반도체 업황에 부정적 환경이 조성되고 있다”고 밝혔다.'],
    ['하드디스크(HDD)의 대안으로 각광받고 있는 SSD(solid state drive)가 반도체 업계의 ‘수출 효자’ 노릇을 하고 있다.', '전문가들은 신종 코로나바이러스 감염증(코로나19) 확산으로 서버 수요가 늘어난 데다 세계 각국이 디지털 인프라 확충에 나서면서 시장 규모가 더욱 커질 것으로 보고 있다.', '17일 산업통상자원부에 따르면 지난달 SSD 수출은 8억3000만달러로 전년 동기 대비 254.5% 급증했다.', '같은 기간 전체 반도체 수출이 15.1% 줄어든 것과는 대조적이다.', 'SSD는 낸드플래시를 활용해 정보를 저장하는 장치다.', '기존 HDD에 비해 정보처리 속도가 빠르고, 부피가 작다. HDD와 달리 기계 구동장치가 없어 열과 소음이 나지 않아 냉각에 필요한 전력을 아낄 수 있다.', 'SSD 수출은 지난해 하반기부터 늘다가 코로나19 이후 폭발적인 증가세를 보이고 있다.', '넷플릭스 등 영상 콘텐츠 소비가 증가해 서버 수요가 급증한 데다 재택근무·온라인 교육용 PC 수요도 늘었다.', '프리미엄 노트북과 데스크톱에는 대부분 SSD가 들어간다.', '작년 기준 노트북의 SSD 적용 비중은 50%다.', '세계 정보기술(IT)업체들도 올 들어 데이터센터에 대한 투자를 늘리면서 기존 HDD를 SSD로 대거 교체하고 있다.', 'JP모간은 최근 낸 보고서를 통해 아마존, 페이스북, 마이크로소프트, 구글의 1분기 데이터센터 투자가 작년 동기 대비 40% 증가했다고 발표했다.', '중국 정부도 올해 5G(5세대) 이동통신과 데이터센터 등 디지털 인프라 구축에 34조위안(약 5900조원)을 쏟아붓기로 했다.', '업계 관계자는 “데이터센터의 물리적 공간을 넓히는 데는 한계가 있다”며 “신규 데이터센터에 들어가는 D램 판매는 정체된 반면 SSD 수출이 증가한 이유”라고 말했다.', '국내 반도체업체들은 낸드 생산량을 늘리며 SSD 시장 공략에 나섰다.', '삼성전자는 중국 시안에 있는 반도체 공장에 80억달러(약 9조5000억원)를 투자해 설비를 증설하고 있다.', '5세대 V낸드를 주로 생산하는 이 공장은 내년 하반기부터 월 생산능력이 웨이퍼 10만 장에서 25만 장으로 늘어난다.', '삼성전자 관계자는 “2분기엔 2TB(테라바이트) 이상 고용량·고부가가치 서버용 SSD 수요 대응에 집중하기로 했다”고 말했다.', 'SK하이닉스의 1분기 SSD 출하량도 12% 증가하며 낸드 매출에서 차지하는 SSD 비중이 처음으로 40%를 넘었다.'],
    ['올 1분기 코로나19 팬데믹(세계적 대유행)에도 글로벌 반도체 업체들이 호실적을 기록했다.', '재택근무 등 비대면 업무환경이 늘어나면서 서버용 반도체 수요가 폭증하자 이들 실적에 긍정적인 영향을 줬기 때문이다.', '인텔, SK하이닉스, 난야, 마이크론테크놀로지 등의 1분기 실적이 그 예다. 다수 메모리 업체들은 2분기에도 서버 호황이 이어질 것으로 예상하고 있다.', '최근 인텔은 올 1분기 경영실적을 발표하고 매출은 198억달러(약 24조4600억원)로 작년 대비 23%나 올랐고, 영업이익은 70억달러(약 8조6500억원)로 지난해 같은 기간 기록한 42억달러보다 무려 69%나 증가했다고 밝혔다.', '특히 서버용 데이터센터그룹(DCG) 성장이 두드러졌다. 이 부문에서 작년 동기 대비 매출 43%나 올랐다.', '인텔은 데이터센터용 제품에서 특히 강세를 띄는 기업이다.', '글로벌 서버용 중앙처리장치(CPU) 시장에서 95% 이상 점유율을 차지하고 있고, 새로운 메모리 장치인 옵테인 DC 퍼시스턴트 메모리도 지난해 출시하며 데이터센터 제품군을 확보했다.', '대용량 저장장치인 솔리드스테이트드라이브(SSD)도 서버 분야에서는 선두권을 달리고 있는 것으로 알려진다.', '최근 실적을 발표한 SK하이닉스도 서버용 D램 판매 호조로 1분기 깜짝 실적을 발표했다.', '영업이익은 8003억원으로 전분기 대비 200% 이상 성장한 데다 당초 시장 컨센서스였던 5000억원대를 대폭 상회하는 실적을 거뒀다.', '글로벌 반도체 업체들이 웃은 이유는 서버용 반도체 제품 수요가 폭증했기 때문이다.', '코로나19로 IT시장 규모가 예상에 비해 쪼그라들었지만, 화상회의나 온라인 교육 등 사용자들이 가정에서 클라우드를 사용해야 할 일이 늘어났다.', '이에 따라 데이터센터 주요 구성 부품인 CPU, D램, 낸드플래시 등 제품 판매가 호조를 띈 것이다.', 'SK하이닉스 관계자는 “서버 제품은 대형 데이터센터 기업 투자 재개와 함께 비대면 업무환경이 조성되면서 코로나19 영향을 상대적으로 덜 받는다”고 설명했다.', '다수 회사들은 앞으로 반도체 시장의 불확실성이 큰 것을 전제하면서도, 2분기 역시 서버용 반도체 제품 실적이 견조할 것으로 전망했다.', '대만업체인 난야의 이페이잉 사장은 “단기적으로 서버, PC, 네트워크 장비 수요는 지속 상승해 스마트폰 D램 수요 감소를 상쇄할 것”이라고 말했다.', '1분기 시장 전망치를 상회한 마이크론테크놀로지 측도 “3분기에도 세계 데이터센터 수요는 상당히 강할 것으로 보이며, 이는 공급 부족 현상을 야기하고 있다”고 설명했다.', '한편 증권업계는 서버 D램 호조에 힘입어 SK하이닉스 영업이익 실적이 2분기 1조원, 3분기 2조원 넘을 것으로 예측했다.', 'D램, 낸드플래시 시장에서 글로벌 1위를 달리고 있는 삼성전자는 29일 실적 발표회를 열고 구체적인 1분기 매출 분석과 함께 서버용 반도체 시장 흐름을 설명할 것으로 보인다.'],
    ['소비자용 SSD(솔리드스테이트드라이브) 시장에서 중화권 기업의 영향력이 커진 것으로 나타났다.', '삼성전자와 SK하이닉스 등이 수익성이 큰 기업용 서버 등 B2B(기업과 기업 간 거래) 시장에 집중하는 사이에, 중국과 대만 기업들이 빠른 속도로 소비자용 시장을 확보하고 있다는 분석이다.', 'SSD란 낸드플래시 반도체를 이용해 디지털 정보를 저장하는 장치로, 최근 PC와 휴대용 저장장치 등의 시장에서 HDD(하드디스크드라이브)를 대체하는 비율이 높아지고 있다.', '17일 업계와 글로벌 시장조사업체 디램익스체인지의 최근 업계 동향 보고서에 따르면 지난해 일반 고객을 상대로 하는 B2C(기업과 소비자 간 거래) 시장에서의 SSD 제품 전 세계 출하량은 5500만개로 집계됐다.', '이는 전년인 2016년 출하량보다 3∼4% 줄어든 규모다.', '업체별로는 삼성전자와 SK하이닉스를 포함해 WDC, 마이크론, 인텔 등 낸드플래시 제조업체들의 지난해 일반 소비자용 SSD 출하량은 전년보다 약 10% 줄었다.', '반면 같은 기간 SSD 모듈 제조업체들의 출하량은 2∼3% 늘어났다.', '이에 따라 지난해 전 세계 전체 SSD 출하량 가운데 낸드플래시 제조업체의 비중은 40%에 그친 반면, 나머지 60%는 모듈 제조업체들이 차지한 것으로 나타났다.', '디램익스체인지 측은 "작년 상반기 나타난 낸드플래시 공급부족 사태가 하반기까지 이어진 탓이 크다"고 설명했다.', '낸드플래시 제조업체들은 시장 호황이 이어지면서 상대적으로 수익성이 높은 서버·데이터센터 OEM(주문자상표부착생산) 부문에 공급물량을 집중한 것으로 보인다.', '그러면서 시장 수요의 상당수를 중화권 모듈 제조업체들이 가져간 것으로 분석된다.', '실제로 낸드플래시 제조업체를 제외하고 SSD 모듈 제조업체들의 지난해 출하량 순위를 살펴본 결과 상위 10위권에서 8개 기업이 모두 중국 또는 대만에 속한 것으로 나타났다.', '대만 기업들은 수익성에 초점을 맞춘 반면, 중국 업체들은 더욱 공격적인 행보로 시장점유율 확대와 인지도 제고에 주력하는 전략상 차이를 보였다.', 'D램익스체인지 측은 "중국 기업들이 생산비용을 낮추고자 SSD 생산을 아웃소싱하고 있다"면서 "낮아진 가격과 함께 올해 풍부한 낸드플래시 공급 상황을 감안할 때, 중국 업체들은 앞으로 시장점유율을 더욱 높일 기회가 있어 보인다"고 예측했다.']
    ]
    # 가격: 0, 신 제품: 1, 프로모션: 2, 업계 동향: 3
    cl_ =[0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]

    key_words_ = []
    key_sentences_ = []
    for i in range(len(cl_)):
        print(i)
        key_words_.append(keyword_extractor(sents_[i], window=2, d_f=0.85, epochs=30, threshold=0.001, T=20))
        key_sentences_.append(keysentence_summarizer(sents_[i], d_f=0.85, epochs=30, threshold=0.001, T=5))
    df_ = pd.DataFrame({'raw': sents_, 'key_word': key_words_, 'key_sentences': key_sentences_, 'classification': cl_[i]})
    df_.to_csv('example_dataset.csv')


if __name__=="__main__":
    #test()
    make_dataset()
